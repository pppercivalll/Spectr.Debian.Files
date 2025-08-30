#!/usr/bin/env python3

import os
import time
import subprocess
import signal
import sys
from pathlib import Path

class BatteryMonitor:
    def __init__(self, battery_path="/sys/class/power_supply/BAT0"):
        self.battery_path = Path(battery_path)
        self.last_status = ""
        self.last_capacity = 0
        self.last_plugged = None 
        self.notification_ids = {
            'battery': 3001,
            'charging': 3002,
            'unplugged': 3003
        }
        
        # Battery level thresholds
        self.critical_level = 15
        self.low_level = 25
        self.warning_level = 40
        
        # Check if battery exists
        if not self.battery_path.exists():
            self.log_message("ERROR: Battery path not found", "error")
            sys.exit(1)
    
    def handle_exit(self, signum, frame):
        """Handle clean exit on signals."""
        self.log_message("Battery monitor shutting down...", "info")
        sys.exit(0)
    
    def log_message(self, message, level="info"):
        """Log message to systemd journal."""
        try:
            subprocess.run([
                'systemd-cat', '-t', 'battery-monitor', '-p', level
            ], input=message.encode(), check=True)
        except Exception:
            print(f"[{level.upper()}] {message}")
    
    def send_notification(self, title, message, icon, urgency="normal", notification_id=None, progress=None):
        """Send desktop notification using dunstify."""
        cmd = [
            'dunstify',
            '-a', 'battery',
            '-u', urgency,
            '-i', icon
        ]
        
        if notification_id:
            cmd.extend(['-r', str(notification_id)])
        
        if progress is not None:
            cmd.extend(['-h', f'int:value:{progress}'])
        
        cmd.extend([title, message])
        
        try:
            subprocess.Popen(cmd)
        except Exception as e:
            self.log_message(f"Notification failed: {str(e)}", "warning")
    
    def get_battery_info(self):
        """Get current battery capacity and status."""
        try:
            capacity = int((self.battery_path / "capacity").read_text().strip())
            status = (self.battery_path / "status").read_text().strip()
            return capacity, status
        except Exception as e:
            self.log_message(f"Error reading battery info: {str(e)}", "error")
            return None, None
    
    def get_ac_adapter_status(self):
        """Check if AC adapter is plugged in."""
        ac_paths = [
            "/sys/class/power_supply/ADP1",
            "/sys/class/power_supply/AC",
            "/sys/class/power_supply/ACAD"
        ]
        
        for ac_path in ac_paths:
            online_file = Path(ac_path) / "online"
            if online_file.exists():
                try:
                    return int(online_file.read_text().strip()) == 1
                except Exception:
                    continue
        
        # Fallback: infer from battery status
        capacity, status = self.get_battery_info()
        if status:
            return status in ["Charging", "Full"]
        
        return None
    
    def get_battery_icon(self, capacity, status):
        """Get appropriate battery icon based on capacity and status."""
        if status == "Charging":
            if capacity >= 90:
                return "battery-level-100-charging-symbolic"
            elif capacity >= 70:
                return "battery-level-90-charging-symbolic"
            elif capacity >= 50:
                return "battery-level-70-charging-symbolic"
            elif capacity >= 30:
                return "battery-level-50-charging-symbolic"
            elif capacity >= 10:
                return "battery-level-30-charging-symbolic"
            else:
                return "battery-level-10-charging-symbolic"
        else:
            if capacity >= 90:
                return "battery-level-100-symbolic"
            elif capacity >= 70:
                return "battery-level-90-symbolic"
            elif capacity >= 50:
                return "battery-level-70-symbolic"
            elif capacity >= 30:
                return "battery-level-50-symbolic"
            elif capacity >= 10:
                return "battery-level-30-symbolic"
            else:
                return "battery-level-10-symbolic"
    
    def get_urgency_level(self, capacity, status):
        """Determine notification urgency based on battery state."""
        if status == "Discharging":
            if capacity <= self.critical_level:
                return "critical"
            elif capacity <= self.low_level:
                return "normal"
        return "low"
    
    def handle_status_change(self, capacity, status, plugged_in):
        """Handle battery status changes."""
        if status == "Discharging":
            if capacity <= self.critical_level:
                self.send_notification(
                    f"⚠️  Critical Battery ({capacity}%)",
                    "Battery critically low! Please plug in charger immediately.",
                    self.get_battery_icon(capacity, status),
                    urgency="critical",
                    notification_id=self.notification_ids['battery'],
                    progress=capacity
                )
                self.log_message(f"⚠️  Critical battery: {capacity}%", "warning")
            
            elif capacity <= self.low_level:
                self.send_notification(
                    f"🔋 Low Battery ({capacity}%)",
                    "Battery is running low. Please connect charger soon.",
                    self.get_battery_icon(capacity, status),
                    urgency="normal",
                    notification_id=self.notification_ids['battery'],
                    progress=capacity
                )
                self.log_message(f"🔋 Low battery: {capacity}%", "info")
            
            elif capacity <= self.warning_level:
                self.send_notification(
                    f"🔋 Battery at {capacity}%",
                    "Consider charging soon.",
                    self.get_battery_icon(capacity, status),
                    urgency="low",
                    notification_id=self.notification_ids['battery'],
                    progress=capacity
                )
                self.log_message(f"ℹ️  Battery warning: {capacity}%", "info")
        
        elif status == "Charging":
            self.send_notification(
                "⚡ Charging",
                f"Battery at {capacity}%",
                self.get_battery_icon(capacity, status),
                urgency="low",
                notification_id=self.notification_ids['charging'],
                progress=capacity
            )
            self.log_message(f"⚡ Charging: {capacity}%", "info")
        
        elif status == "Full":
            self.send_notification(
                "✅ Battery Full",
                "Battery is fully charged. You can unplug the charger.",
                self.get_battery_icon(capacity, status),
                urgency="low",
                notification_id=self.notification_ids['charging'],
                progress=100
            )
            self.log_message(f"✅ Battery full: {capacity}%", "info")
    
    def handle_unplug_event(self, capacity):
        """Handle charger unplugged event."""
        if capacity >= 90:
            urgency = "low"
            message = "Charger unplugged. Battery is well charged."
        elif capacity >= 50:
            urgency = "normal"
            message = f"Charger unplugged. Battery at {capacity}%."
        else:
            urgency = "normal"
            message = f"Charger unplugged. Battery at {capacity}% - monitor usage."
        
        self.send_notification(
            f"🔌 Charger Unplugged",
            message,
            self.get_battery_icon(capacity, "Discharging"),
            urgency=urgency,
            notification_id=self.notification_ids['unplugged'],
            progress=capacity
        )
        self.log_message(f"🔌 Charger unplugged at {capacity}%", "info")
    
    def should_notify(self, capacity, status, plugged_in):
        """Determine if notification should be sent."""
        status_changed = status != self.last_status
        capacity_change = abs(capacity - self.last_capacity) >= 10
        plug_state_changed = plugged_in != self.last_plugged
        
        # Always notify on status change
        if status_changed:
            return True
        
        # Notify on significant capacity changes during discharge
        if status == "Discharging" and capacity_change:
            return True
        
        # Notify on plug state changes
        if plug_state_changed and self.last_plugged is not None:
            return True
        
        return False
    
    def run(self):
        """Main monitoring loop."""
        self.log_message("Battery monitor started", "info")
        
        # Set up signal handlers
        signal.signal(signal.SIGTERM, self.handle_exit)
        signal.signal(signal.SIGINT, self.handle_exit)
        
        # Initialize state
        capacity, status = self.get_battery_info()
        if capacity is None:
            return
        
        self.last_capacity = capacity
        self.last_status = status
        self.last_plugged = self.get_ac_adapter_status()
        
        self.log_message(f"Initial state: {status} {capacity}%, AC: {'Connected' if self.last_plugged else 'Disconnected'}", "info")
        
        while True:
            try:
                capacity, status = self.get_battery_info()
                if capacity is None or status is None:
                    time.sleep(5)
                    continue
                
                plugged_in = self.get_ac_adapter_status()
                
                # Check for unplug event (AC was connected, now disconnected)
                if (self.last_plugged is True and plugged_in is False and 
                    status == "Discharging"):
                    self.handle_unplug_event(capacity)
                
                # Send notifications based on conditions
                if self.should_notify(capacity, status, plugged_in):
                    self.handle_status_change(capacity, status, plugged_in)
                
                # Update tracking variables
                self.last_status = status
                self.last_capacity = capacity
                self.last_plugged = plugged_in
                
                time.sleep(2)  # Check every 2 seconds
                
            except KeyboardInterrupt:
                self.handle_exit(signal.SIGINT, None)
            except Exception as e:
                self.log_message(f"Unexpected error: {str(e)}", "error")
                time.sleep(5)


if __name__ == "__main__":
    monitor = BatteryMonitor()
    monitor.run()
