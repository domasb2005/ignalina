#!/bin/bash
echo "y" | sudo pwmconfig

# Sleep for 5 seconds
sleep 8

# Terminate the script itself
sudo pkill pwmconfig
