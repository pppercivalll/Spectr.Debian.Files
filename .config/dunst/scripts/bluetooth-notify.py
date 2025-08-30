#!/usr/bin/env python3

import dbus
import dbus.mainloop.glib
from gi.repository import GLib
import subprocess
import os
import signal
import sys
import time
from pathlib import Path
import json

class BluetoothMonitor:
    def __init__(self):
        self.bus = None
        self.loop = None
        self.device_cache = {}
        self.notification_ids = {
            'adapter': 4001,
            'device': 4002,
            'pairing': 4003,
            'audio': 4004
        }
        
        # Configuration
        self.config_dir = Path.home() / ".config" / "bluetooth-notify"
        self.config_file = self.config_dir / "config.json"
        self.device_history_file = self.config_dir / "device_history.json"
        
        # Load configuration
        self.load_config()
        
        # Device history for smart notifications
        self.device_history = self.load_device_history()
        
        # Set up D-Bus
        self.setup_dbus()
    
    def load_config(self):
        """Load configuration from file or use defaults."""
        default_config = {
            "show_adapter_events": True,
            "show_pairing_events": True,
            "show_audio_events": True,
            "show_device_info": True,
            "notification_timeout": 5000,
            "audio_device_types": ["headset", "headphones", "speaker", "audio"]
        }
        
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    user_config = json.load(f)
                    default_config.update(user_config)
        except Exception as e:
            self.log_message(f"Warning: Could not load config: {e}", "warning")
        
        self.config = default_config
        self.save_config()
    
    def save_config(self):
        """Save configuration to file."""
        try:
            self.config_dir.mkdir(exist_ok=True)
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            self.log_message(f"Warning: Could not save config: {e}", "warning")
    
    def load_device_history(self):
        """Load device connection history."""
        try:
            if self.device_history_file.exists():
                with open(self.device_history_file, 'r') as f:
                    return json.load(f)
        except Exception:
            pass
        return {}
    
    def save_device_history(self):
        """Save device connection history."""
        try:
            self.config_dir.mkdir(exist_ok=True)
            with open(self.device_history_file, 'w') as f:
                json.dump(self.device_history, f, indent=2)
        except Exception as e:
            self.log_message(f"Warning: Could not save device history: {e}", "warning")
    
    def setup_dbus(self):
        """Set up D-Bus connection and main loop."""
        try:
            dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
            self.bus = dbus.SystemBus()
            self.loop = GLib.MainLoop()
        except Exception as e:
            self.log_message(f"Failed to setup D-Bus: {e}", "error")
            sys.exit(1)
    
    def handle_exit(self, signum, frame):
        """Handle clean exit on signals."""
        self.log_message("Bluetooth monitor shutting down...", "info")
        self.save_device_history()
        if self.loop:
            self.loop.quit()
        sys.exit(0)
    
    def log_message(self, message, level="info"):
        """Log message to systemd journal."""
        try:
            subprocess.run([
                'systemd-cat', '-t', 'bluetooth-notify', '-p', level
            ], input=message.encode(), check=True)
        except Exception:
            print(f"[{level.upper()}] {message}")
    
    def send_notification(self, title, message, icon="bluetooth", urgency="normal", 
                         notification_id=None, timeout=None, actions=None):
        """Send desktop notification using dunstify."""
        cmd = [
            'dunstify',
            '-a', 'Bluetooth',
            '-i', icon,
            '-u', urgency
        ]
        
        if notification_id:
            cmd.extend(['-r', str(notification_id)])
        
        if timeout or self.config.get('notification_timeout'):
            cmd.extend(['-t', str(timeout or self.config['notification_timeout'])])
        
        if actions:
            for action_id, action_label in actions.items():
                cmd.extend(['-A', f'{action_id},{action_label}'])
        
        cmd.extend([title, message])
        
        try:
            subprocess.Popen(cmd)
        except Exception as e:
            self.log_message(f"Notification failed: {str(e)}", "warning")
    
    def get_device_info(self, device_path):
        """Get comprehensive device information with caching."""
        if device_path in self.device_cache:
            cache_entry = self.device_cache[device_path]
            # Use cache if less than 30 seconds old
            if time.time() - cache_entry['timestamp'] < 30:
                return cache_entry['info']
        
        try:
            device_props = dbus.Interface(
                self.bus.get_object('org.bluez', device_path),
                'org.freedesktop.DBus.Properties'
            )
            
            info = {
                'alias': str(device_props.Get('org.bluez.Device1', 'Alias')),
                'address': str(device_props.Get('org.bluez.Device1', 'Address')),
                'connected': bool(device_props.Get('org.bluez.Device1', 'Connected')),
                'paired': bool(device_props.Get('org.bluez.Device1', 'Paired')),
                'trusted': bool(device_props.Get('org.bluez.Device1', 'Trusted')),
                'rssi': None,
                'battery_level': None,
                'device_class': None,
                'uuids': []
            }
            
            # Get optional properties
            try:
                info['rssi'] = int(device_props.Get('org.bluez.Device1', 'RSSI'))
            except:
                pass
            
            try:
                info['battery_level'] = int(device_props.Get('org.bluez.Battery1', 'Percentage'))
            except:
                pass
            
            try:
                info['device_class'] = int(device_props.Get('org.bluez.Device1', 'Class'))
            except:
                pass
            
            try:
                info['uuids'] = [str(uuid) for uuid in device_props.Get('org.bluez.Device1', 'UUIDs')]
            except:
                pass
            
            # Cache the result
            self.device_cache[device_path] = {
                'info': info,
                'timestamp': time.time()
            }
            
            return info
            
        except Exception as e:
            self.log_message(f"Error getting device info for {device_path}: {e}", "warning")
            return {
                'alias': "Unknown Device",
                'address': "",
                'connected': False,
                'paired': False,
                'trusted': False,
                'rssi': None,
                'battery_level': None,
                'device_class': None,
                'uuids': []
            }
    
    def get_adapter_info(self, adapter_path):
        """Get adapter information."""
        try:
            adapter_props = dbus.Interface(
                self.bus.get_object('org.bluez', adapter_path),
                'org.freedesktop.DBus.Properties'
            )
            return {
                'alias': str(adapter_props.Get('org.bluez.Adapter1', 'Alias')),
                'address': str(adapter_props.Get('org.bluez.Adapter1', 'Address')),
                'powered': bool(adapter_props.Get('org.bluez.Adapter1', 'Powered')),
                'discoverable': bool(adapter_props.Get('org.bluez.Adapter1', 'Discoverable')),
                'pairable': bool(adapter_props.Get('org.bluez.Adapter1', 'Pairable'))
            }
        except Exception as e:
            self.log_message(f"Error getting adapter info: {e}", "warning")
            return {'alias': "Bluetooth Adapter", 'powered': False}
    
    def is_audio_device(self, device_info):
        """Check if device is an audio device based on UUIDs and class."""
        audio_uuids = [
            "0000110b-0000-1000-8000-00805f9b34fb",  # Audio Sink
            "0000110e-0000-1000-8000-00805f9b34fb",  # A/V Remote Control
            "0000111e-0000-1000-8000-00805f9b34fb",  # Handsfree
            "00001108-0000-1000-8000-00805f9b34fb",  # Headset
            "0000110a-0000-1000-8000-00805f9b34fb",  # Audio Source
        ]
        
        # Check UUIDs
        for uuid in device_info.get('uuids', []):
            if uuid.lower() in [u.lower() for u in audio_uuids]:
                return True
        
        # Check device class
        device_class = device_info.get('device_class')
        if device_class:
            # Major device class for audio/video devices is 0x04
            major_class = (device_class >> 8) & 0x1F
            if major_class == 0x04:
                return True
        
        # Check alias for audio keywords
        alias = device_info.get('alias', '').lower()
        audio_keywords = self.config.get('audio_device_types', [])
        return any(keyword in alias for keyword in audio_keywords)
    
    def get_device_icon(self, device_info):
        """Get appropriate icon for device type."""
        if self.is_audio_device(device_info):
            if device_info.get('connected'):
                return "audio-headphones-bluetooth-symbolic"
            else:
                return "audio-headphones-symbolic"
        
        device_class = device_info.get('device_class')
        if device_class:
            major_class = (device_class >> 8) & 0x1F
            minor_class = (device_class >> 2) & 0x3F
            
            if major_class == 0x01:  # Computer
                return "computer-symbolic"
            elif major_class == 0x02:  # Phone
                return "phone-symbolic"
            elif major_class == 0x05:  # Peripheral (mouse, keyboard)
                if minor_class & 0x40:  # Pointing device
                    return "input-mouse-symbolic"
                elif minor_class & 0x10:  # Keyboard
                    return "input-keyboard-symbolic"
                return "input-gaming-symbolic"
        
        # Default bluetooth icon
        return "bluetooth-symbolic" if device_info.get('connected') else "bluetooth-disabled-symbolic"
    
    def update_device_history(self, device_info):
        """Update device connection history."""
        address = device_info.get('address')
        if not address:
            return
        
        if address not in self.device_history:
            self.device_history[address] = {
                'alias': device_info.get('alias'),
                'first_seen': time.time(),
                'connection_count': 0,
                'last_connected': None,
                'is_frequent': False
            }
        
        history = self.device_history[address]
        history['alias'] = device_info.get('alias')  # Update alias
        
        if device_info.get('connected'):
            history['connection_count'] += 1
            history['last_connected'] = time.time()
            history['is_frequent'] = history['connection_count'] >= 5
    
    def handle_adapter_change(self, adapter_path, powered):
        """Handle Bluetooth adapter power state changes."""
        if not self.config.get('show_adapter_events', True):
            return
        
        adapter_info = self.get_adapter_info(adapter_path)
        alias = adapter_info.get('alias', 'Bluetooth Adapter')
        
        if powered:
            self.send_notification(
                ">ᛒ Bluetooth Enabled",
                f"{alias} is now <b>ON</b>",
                "bluetooth-active",
                urgency="low",
                notification_id=self.notification_ids['adapter']
            )
            self.log_message(f"Bluetooth adapter '{alias}' powered ON", "info")
        else:
            self.send_notification(
                ">ᛒ Bluetooth Disabled",
                f"{alias} is now <b>OFF</b>",
                "bluetooth-disabled",
                urgency="low",
                notification_id=self.notification_ids['adapter']
            )
            self.log_message(f"Bluetooth adapter '{alias}' powered OFF", "info")
    
    def handle_device_connection_change(self, device_path, connected):
        """Handle device connection state changes."""
        device_info = self.get_device_info(device_path)
        alias = device_info.get('alias', 'Unknown Device')
        address = device_info.get('address', '')
        
        self.update_device_history(device_info)
        
        if connected:
            # Connection established
            icon = self.get_device_icon(device_info)
            battery_info = ""
            
            if device_info.get('battery_level') is not None:
                battery_info = f" (Battery: {device_info['battery_level']}%)"
            
            signal_info = ""
            if device_info.get('rssi') is not None:
                signal_strength = "Strong" if device_info['rssi'] > -60 else "Weak" if device_info['rssi'] < -80 else "Good"
                signal_info = f" • Signal: {signal_strength}"
            
            message_parts = [f"Device <b>Connected</b>{battery_info}"]
            if self.config.get('show_device_info', True) and (battery_info or signal_info):
                message_parts.append(signal_info)
            
            message = "".join(message_parts)
            
            # Check if it's an audio device for special handling
            if self.is_audio_device(device_info) and self.config.get('show_audio_events', True):
                self.send_notification(
                    f"🎧 {alias}",
                    message,
                    icon,
                    urgency="normal",
                    notification_id=self.notification_ids['audio'],
                    actions={"disconnect": "Disconnect"}
                )
                self.log_message(f"Audio device connected: {alias} ({address})", "info")
            else:
                self.send_notification(
                    f"📱 {alias}",
                    message,
                    icon,
                    urgency="low",
                    notification_id=self.notification_ids['device']
                )
                self.log_message(f"Device connected: {alias} ({address})", "info")
        
        else:
            # Connection lost
            icon = self.get_device_icon(device_info)
            
            if self.is_audio_device(device_info) and self.config.get('show_audio_events', True):
                self.send_notification(
                    f"🎧 {alias}",
                    "Audio device <b>Disconnected</b>",
                    icon,
                    urgency="normal",
                    notification_id=self.notification_ids['audio']
                )
                self.log_message(f"Audio device disconnected: {alias} ({address})", "info")
            else:
                self.send_notification(
                    f"📱 {alias}",
                    "Device <b>Disconnected</b>",
                    icon,
                    urgency="low",
                    notification_id=self.notification_ids['device']
                )
                self.log_message(f"Device disconnected: {alias} ({address})", "info")
    
    def handle_device_pairing_change(self, device_path, paired):
        """Handle device pairing state changes."""
        if not self.config.get('show_pairing_events', True):
            return
        
        device_info = self.get_device_info(device_path)
        alias = device_info.get('alias', 'Unknown Device')
        address = device_info.get('address', '')
        
        if paired:
            self.send_notification(
                f"🔗 {alias}",
                "Device <b>Paired</b> successfully",
                "dialog-information",
                urgency="normal",
                notification_id=self.notification_ids['pairing']
            )
            self.log_message(f"Device paired: {alias} ({address})", "info")
        else:
            self.send_notification(
                f"🔗 {alias}",
                "Device <b>Unpaired</b>",
                "dialog-warning",
                urgency="normal",
                notification_id=self.notification_ids['pairing']
            )
            self.log_message(f"Device unpaired: {alias} ({address})", "info")
    
    def properties_changed(self, interface, changed, invalidated, path):
        """Handle D-Bus property changes."""
        try:
            if interface == 'org.bluez.Adapter1':
                if 'Powered' in changed:
                    self.handle_adapter_change(path, changed['Powered'])
            
            elif interface == 'org.bluez.Device1':
                if 'Connected' in changed:
                    self.handle_device_connection_change(path, changed['Connected'])
                if 'Paired' in changed:
                    self.handle_device_pairing_change(path, changed['Paired'])
                
                # Clear cache when device properties change
                if path in self.device_cache:
                    del self.device_cache[path]
        
        except Exception as e:
            self.log_message(f"Error handling property change: {e}", "warning")
    
    def discover_existing_devices(self):
        """Discover and log existing paired/connected devices on startup."""
        try:
            manager = dbus.Interface(
                self.bus.get_object('org.bluez', '/'),
                'org.freedesktop.DBus.ObjectManager'
            )
            
            objects = manager.GetManagedObjects()
            connected_devices = []
            paired_devices = []
            
            for path, interfaces in objects.items():
                if 'org.bluez.Device1' in interfaces:
                    device_info = self.get_device_info(path)
                    if device_info.get('connected'):
                        connected_devices.append(device_info.get('alias', 'Unknown'))
                    elif device_info.get('paired'):
                        paired_devices.append(device_info.get('alias', 'Unknown'))
            
            if connected_devices:
                self.log_message(f"Connected devices at startup: {', '.join(connected_devices)}", "info")
            if paired_devices:
                self.log_message(f"Paired devices: {len(paired_devices)} total", "info")
                
        except Exception as e:
            self.log_message(f"Error discovering existing devices: {e}", "warning")
    
    def run(self):
        """Main monitoring loop."""
        self.log_message("Bluetooth monitor started", "info")
        
        # Set up signal handlers
        signal.signal(signal.SIGTERM, self.handle_exit)
        signal.signal(signal.SIGINT, self.handle_exit)
        
        try:
            # Discover existing devices
            self.discover_existing_devices()
            
            # Listen for BlueZ property changes
            self.bus.add_signal_receiver(
                self.properties_changed,
                signal_name='PropertiesChanged',
                dbus_interface='org.freedesktop.DBus.Properties',
                path_keyword='path'
            )
            
            # Start the main loop
            self.log_message("Monitoring Bluetooth events...", "info")
            self.loop.run()
            
        except Exception as e:
            self.log_message(f"Error in main loop: {str(e)}", "error")
            self.handle_exit(signal.SIGTERM, None)


if __name__ == "__main__":
    try:
        monitor = BluetoothMonitor()
        monitor.run()
    except KeyboardInterrupt:
        print("\nShutting down...")
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)
