## Initial setup

clone repository
nano ~/.xinitrc
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

cd ignalina
python3 gameflow/gameloop3.py
install missing libraries system wide with apt
sudo apt update
sudo apt install mosquitto mosquitto-clients
sudo systemctl start mosquitto
sudo systemctl enable mosquitto
sudo nano /etc/mosquitto/mosquitto.conf
	listener 1883
	allow_anonymous true
sudo systemctl restart mosquitto

make sure raspberry pico is on the same network as broker
make sure broker address is up to date in pico code

from ssh:
DISPLAY=:0.0 pavucontrol &