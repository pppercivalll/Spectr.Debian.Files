#!/usr/bin/env python3

import dbus
from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import GLib
import subprocess
import os
import signal

# File to store last connection
CONNECTION_FILE = os.path.expanduser("~/.config/dunst/last_connection")

# Global variable to track current connection
current_connection = None

def handle_exit(signum, frame):
    loop.quit()

signal.signal(signal.SIGTERM, handle_exit)
signal.signal(signal.SIGINT, handle_exit)

def send_notification(title, message, icon):
    try:
        subprocess.Popen([
            'dunstify', 
            '-a', 'Network Manager',
            '-i', icon,
            '-r', '12345',
            title,
            message
        ])
    except Exception as e:
        print(f"Notification failed: {str(e)}")

def get_active_connection():
    """Get currently active connection name and type."""
    try:
        output = subprocess.check_output(
            ['nmcli', '-t', '-f', 'NAME,DEVICE,TYPE', 'con', 'show', '--active'],
            text=True
        )
        for line in output.splitlines():
            if not line or 'lo:' in line or 'tun' in line or 'virbr' in line:
                continue
            parts = line.split(':')
            if len(parts) >= 3:
                return parts[0], parts[2]
        return None, None
    except Exception as e:
        print(f"Error getting active connection: {e}")
        return None, None

def save_connection(name):
    """Save current connection to file."""
    try:
        os.makedirs(os.path.dirname(CONNECTION_FILE), exist_ok=True)
        with open(CONNECTION_FILE, 'w') as f:
            f.write(name)
    except Exception as e:
        print(f"Error saving connection: {e}")

def get_last_connection():
    """Get last saved connection."""
    try:
        with open(CONNECTION_FILE, 'r') as f:
            return f.read().strip()
    except:
        return None

def get_network_icon(conn_type):
    """Get appropriate icon based on connection type."""
    if not conn_type:
        return "network-wireless"
    
    conn_type = conn_type.lower()
    if 'wireless' in conn_type or 'wifi' in conn_type:
        return "network-wireless"
    elif 'ethernet' in conn_type or 'wired' in conn_type:
        return "network-wired"
    elif 'vpn' in conn_type:
        return "network-vpn"
    else:
        return "network-wireless"

def check_connection_change():
    """Check for connection changes and send notifications."""
    global current_connection
    
    conn_name, conn_type = get_active_connection()
    
    # Connection established
    if conn_name and conn_name != current_connection:
        if current_connection:
            send_notification(
                "📡 Network Manager",
                f"Disconnected from <b>{current_connection}</b>",
                "network-wireless-disconnected"
            )
        
        # Notify about new connection
        current_connection = conn_name
        save_connection(conn_name)
        icon = get_network_icon(conn_type)
        send_notification(
            "📡 Network Manager",
            f"Connected to <b>{conn_name}</b>",
            icon
        )
    
    # Connection lost
    elif not conn_name and current_connection:
        send_notification(
            "📡 Network Manager",
            f"Disconnected from <b>{current_connection}</b>",
            "network-wireless-disconnected"
        )
        current_connection = None
        try:
            os.remove(CONNECTION_FILE)
        except:
            pass
    
    return False

def state_changed_handler(state):
    """Handle NetworkManager state changes."""
    print(f"NetworkManager state changed to: {state}")
    
    GLib.timeout_add(500, check_connection_change)

def connection_state_changed(nm_active_connection, state, reason):
    """Handle individual connection state changes."""
    print(f"Connection state changed: {state}")
    GLib.timeout_add(200, check_connection_change)

def initialize_current_connection():
    """Initialize the current connection state."""
    global current_connection
    conn_name, _ = get_active_connection()
    current_connection = conn_name
    if conn_name:
        save_connection(conn_name)

if __name__ == "__main__":
    try:
        DBusGMainLoop(set_as_default=True)
        bus = dbus.SystemBus()
        
        # Initialize current connection state
        initialize_current_connection()
        
        # Listen for NetworkManager state changes
        bus.add_signal_receiver(
            state_changed_handler,
            signal_name="StateChanged",
            dbus_interface="org.freedesktop.NetworkManager",
            path="/org/freedesktop/NetworkManager"
        )
        
        # Also listen for active connection changes (more reliable)
        try:
            bus.add_signal_receiver(
                connection_state_changed,
                signal_name="StateChanged",
                dbus_interface="org.freedesktop.NetworkManager.Connection.Active"
            )
        except Exception as e:
            print(f"Warning: Could not listen for connection state changes: {e}")
        
        # Start main loop
        loop = GLib.MainLoop()
        print("Monitoring NetworkManager events...")
        print(f"Current connection: {current_connection}")
        loop.run()
        
    except Exception as e:
        print(f"Error: {str(e)}")
        send_notification(
            "Network Manager Error", 
            f"Monitor failed: {str(e)}",
            "dialog-error"
        )
