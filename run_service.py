#!/usr/bin/env python3

from time import sleep
import subprocess
import json
from pathlib import Path
from typing import Optional
import concurrent.futures
import logging
import threading

root_path = Path('/home/pi/rfid_jukebox')
player: Optional[subprocess.Popen] = None


def wait_for_end(player_process):
    global player, player_lock
    player_process.wait()

    if player_process.returncode == 0:
        player_lock.acquire()
        if player == player_process:
            player = None
        player_lock.release()
        logging.info(f"Playback stopped")


def play_audio(audio_file: Path, audio_device: Optional[str]):
    global player, polling_executor

    player_lock.acquire()
    if player:
        try:
            player.terminate()
            player.wait(timeout=0.5)
        except subprocess.TimeoutExpired:
            player.kill()
            sleep(0.5)
            if player.returncode is None:
                player.kill()
        player = None

    logging.info(f"Starts playing {audio_file}")
    run_args = ["mpg123"]
    if audio_device is not None:
        run_args += ["-a", audio_device]
    run_args += [audio_file]

    player = subprocess.Popen(run_args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    # set polling
    polling_executor.submit(wait_for_end, player)

    player_lock.release()

def set_sound_volume(set_sound_volume_percent):
    # get info about max level
    logging.info(f"Set volume: trying")
    sound_volume_query = subprocess.run(['amixer', 'cset', 'numid=1'], capture_output=True, encoding='utf-8')
    if sound_volume_query.returncode == 0:
        logging.info(f"Set volume: amixer query success")
        parsed_key_values = {}
        for line in sound_volume_query.stdout.splitlines():
            parsed_key_values.update(dict([tuple(item.split("=", 1)) for item in line.split(",")]))
        if 'min' in parsed_key_values and 'max' in parsed_key_values:
            logging.info(f"Set volume: amixer query contains min and max")
            min_volume = int(parsed_key_values['min'])
            max_volume = int(parsed_key_values['max'])
            target_value = min_volume + set_sound_volume_percent * (max_volume-min_volume)/100
            sound_volume_set_query = subprocess.run(
                ['amixer', 'cset', 'numid=1', '--', str(target_value)],
                capture_output=True,
                encoding='utf-8')
            if sound_volume_set_query.returncode == 0:
                logging.info(f"Set volume: success ({set_sound_volume_percent}%)")


try:
    logging.basicConfig(level=logging.INFO, encoding='utf-8')
    logging.info('Starting service')

    with open(Path(root_path, 'service.config.json')) as config_file:
        config = json.load(config_file)
    try:
        sound_volume_percent = float(config['soundVolumePercent'])
    except (TypeError, KeyError):
        sound_volume_percent = None

    try:
        audio_device = config['audioDevice'].strip()
    except KeyError:
        audio_device = None

    if sound_volume_percent is not None and 0 <= sound_volume_percent <= 100:
        set_sound_volume(sound_volume_percent)

    # tracks is an object with key = rfid tag, value = audio to play
    tracks = config['tracks']

    player = None
    player_lock = threading.Lock()
    polling_executor = concurrent.futures.ThreadPoolExecutor(max_workers=5)

    with open("/dev/tty0", "r") as tty0:
        while True:
            line = tty0.readline()
            rfid_id = line.strip()
            if rfid_id in tracks:
                audio_path = Path(root_path, "audio", tracks[rfid_id])
                play_audio(audio_path, audio_device)
            else:
                logging.warning(f"Unknown input")
    pause()

except KeyboardInterrupt:
    pass
except BaseException as err:
    with open(Path(root_path, 'ERROR_LOG.txt'), 'a') as error_log:
        print(f"{err=}, {type(err)=}", file=error_log, end="\r\n", flush=True)
        logging.error(f"{err=}, {type(err)=}")
    sleep(60)
finally:
    logging.warning("Shutting down")
    polling_executor.shutdown(wait=True)
