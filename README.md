## Installation

### Dependencies

#### Software
##### mpg123 audio player
```bash
sudo apt install mpg123
```

##### Hardware
RFID reader identifying as a HID (Human Interface Device - a Keyboard)

#### Disable the console (tty) login
The login would steal the characters coming from the RFID reader
```bash
sudo systemctl disable --now getty@tty1
sudo systemctl disable --now getty@tty0
```

### Copy this to a fresh Raspberry
From this repo to a ssh-enabled Raspberry.
```bash
rsync -r . pi@192.168.1.165:/home/pi/rfid_jukebox
```
Alternatively
  * checkout the repo on the raspberry
  * or copy this to the /home/pi/rfid_jukebox folder on the sd card

### Set as a service (autostart)
In the Raspberry PI:
```bash
sudo cp service/rfid_jukebox.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable rfid_jukebox
sudo systemctl start rfid_jukebox
```
