import pygame
import subprocess
import time

# Mapping device names to indices
DEVICE_MAP = {
    "phone": "alsa_output.usb-C-Media_Electronics_Inc._USB_PnP_Sound_Device-00.analog-stereo-output",
    "ringer": "alsa_output.pci-0000_00_1b.0.analog-stereo",
    "speaker": "alsa_output.usb-GeneralPlus_USB_Audio_Device-00.analog-stereo"
}

def set_default_sink(sink_name):
    """Set the default audio sink (output device)."""
    try:
        subprocess.run(["pactl", "set-default-sink", sink_name], check=True)
        print(f"Default sink set to: {sink_name}")
    except subprocess.CalledProcessError as e:
        print(f"Error setting default sink: {e}")

def play_through_specific(deviceName, volume, loop, file):
    """
    Play audio through a specific device with specified volume and looping option.

    Args:
        deviceName (str): Name of the device ('phone', 'ringer', 'speaker').
        volume (int): Volume level (0-100).
        loop (bool): Whether to loop the audio indefinitely.
        file (str): Path to the audio file.
    """
    if deviceName not in DEVICE_MAP:
        print(f"Error: Unknown device name '{deviceName}'. Choose from {list(DEVICE_MAP.keys())}.")
        return

    # Set the audio sink
    sink_name = DEVICE_MAP[deviceName]
    set_default_sink(sink_name)

    # Initialize pygame mixer
    pygame.mixer.init()
    pygame.mixer.music.load(file)
    pygame.mixer.music.set_volume(volume / 100.0)  # Set volume (0.0 to 1.0)

    # Start playback
    loops = -1 if loop else 0  # -1 for infinite looping
    pygame.mixer.music.play(loops=loops)
    print(f"Playing {file} on {deviceName} ({sink_name}) with volume {volume}%")

    try:
        while pygame.mixer.music.get_busy():
            time.sleep(1)  # Keep the program alive while music is playing
    except KeyboardInterrupt:
        print("\nStopping playback.")
        pygame.mixer.music.stop()
        pygame.mixer.quit()

if __name__ == "__main__":
    # Example: Play on "speaker" with 80% volume, looping enabled
    play_through_specific("ringer", 100, True, "ring.mp3")
