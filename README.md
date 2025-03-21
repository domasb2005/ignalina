## Initial setup

**clone repository**  

**edit `.xinitrc` file**  
```bash
nano ~/.xinitrc
```

Example `.xinitrc`:
```bash
sleep 5
cd ~/ignalina
python3 -m gunicorn main:app -b 0.0.0.0:5000 &
./run_loop.sh &
#xrandr --output VGA-1 --pos 0x0 --output LVDS-1 --pos 6250x0
xrandr --output HDMI-1 --auto --primary
xset -dpms
xset s off
xset s noblank
openbox-session
#bash ~/mousekeep.sh &
```

**navigate to project directory and run game loop**  
```bash
cd ignalina
python3 gameflow/gameloop3.py
```

**install missing libraries system wide with apt**  
```bash
sudo apt update
sudo apt install mosquitto mosquitto-clients
```

**start and enable Mosquitto service**  
```bash
sudo systemctl start mosquitto
sudo systemctl enable mosquitto
```

**edit Mosquitto configuration**  
```bash
sudo nano /etc/mosquitto/mosquitto.conf
```

Inside the config file, add:
```bash
listener 1883
allow_anonymous true
```

**restart Mosquitto**  
```bash
sudo systemctl restart mosquitto
```

**make sure Raspberry Pico is on the same network as broker**

**make sure broker address is up to date in Pico code**

**from SSH, open PulseAudio control panel and find sound card names**  
```bash
DISPLAY=:0.0 pavucontrol &
```

