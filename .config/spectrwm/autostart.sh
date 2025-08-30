#!/bin/bash

# Notification Daemon  
dunst &

# Wallpapers
feh --bg-fill --randomize ~/Pictures/Wallpapers/* &

# Policy Kit
# /usr/bin/lxpolkit &

# Animations
picom &

# Bluetooth Notification
~/.config/dunst/scripts/bluetooth-notify.py &

# Network Notification
~/.config/dunst/scripts/nm-notify.py &

# Battery Notification
~/.config/dunst/scripts/battery-monitor.py &

# Music Player Notification
~/.config/dunst/scripts/music-player-notify.py &

# Download Notification
~/.config/dunst/scripts/download-notify.py &

# Screenshot Notification
# ~/.config/dunst/scripts/screenshot_notify.py &

# Lock
xautolock -detectsleep -time 15 -locker "/home/annpenrose/.config/i3/i3lock/lock.sh"
