## Installation

### Dependencies

#### Software
##### mpg123 audio player
```bash
sudo apt install mpg123
```

##### Hardware
RFID reader identifying as a HID (Human Interface Device - a Keyboard)

##### Disable the console (tty) login
The login would steal the characters coming from the RFID reader
```bash
sudo systemctl disable --now getty@tty1
sudo systemctl disable --now getty@tty0
```
