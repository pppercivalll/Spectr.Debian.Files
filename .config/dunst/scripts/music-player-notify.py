#!/usr/bin/env python3

import dbus
import dbus.mainloop.glib
from gi.repository import GLib
import subprocess
import signal
import sys
import time
import urllib.parse
import hashlib
from pathlib import Path

class MusicPlayerMonitor:
    def __init__(self):
        self.bus = None
        self.loop = None
        self.current_track_signature = None
        self.last_playback_status = None
        
        # Notification settings
        self.notification_id = 7001
        self.timeout = 2000
        
        # Album art cache
        self.cache_dir = Path.home() / ".cache" / "music-notify" / "covers"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.setup_dbus()
    
    def setup_dbus(self):
        try:
            dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
            self.bus = dbus.SessionBus()
            self.loop = GLib.MainLoop()
        except Exception as e:
            print(f"Failed to setup D-Bus: {e}")
            sys.exit(1)
    
    def handle_exit(self, signum, frame):
        if self.loop:
            self.loop.quit()
        sys.exit(0)
    
    def send_notification(self, title, message, icon="audio-x-generic"):
        cmd = [
            'dunstify',
            '-a', 'music',
            '-i', icon,
            '-u', 'normal',
            '-t', str(self.timeout),
            '-r', str(self.notification_id),
            title, message
        ]
        
        try:
            subprocess.Popen(cmd)
        except Exception as e:
            print(f"Notification failed: {e}")
    
    def get_album_art_path(self, art_url):
        if not art_url or not art_url.startswith(('http://', 'https://', 'file://')):
            return None
        try:
            url_hash = hashlib.md5(art_url.encode()).hexdigest()
            cache_file = self.cache_dir / f"{url_hash}.jpg"
            
            if cache_file.exists():
                return str(cache_file)
            
            if art_url.startswith('file://'):
                local_path = urllib.parse.unquote(art_url[7:])
                if Path(local_path).exists():
                    subprocess.run(['cp', local_path, str(cache_file)], check=True)
                    return str(cache_file)
            else:
                subprocess.run([
                    'curl', '-s', '-o', str(cache_file), 
                    '--max-time', '5', art_url
                ], check=True)
                return str(cache_file)
        except:
            pass
        return None
    
    def get_track_signature(self, metadata):
        """Create unique signature for a track"""
        title = str(metadata.get('xesam:title', ''))
        artist = ', '.join([str(a) for a in metadata.get('xesam:artist', [])])
        album = str(metadata.get('xesam:album', ''))
        track_id = str(metadata.get('mpris:trackid', ''))
        url = str(metadata.get('xesam:url', ''))
        
        return f"{title}|{artist}|{album}|{track_id}|{url}"
    
    def get_player_info(self, player_name):
        try:
            player = self.bus.get_object(player_name, '/org/mpris/MediaPlayer2')
            props = dbus.Interface(player, 'org.freedesktop.DBus.Properties')
            metadata = props.Get('org.mpris.MediaPlayer2.Player', 'Metadata')
            playback_status = props.Get('org.mpris.MediaPlayer2.Player', 'PlaybackStatus')
            
            try:
                identity = props.Get('org.mpris.MediaPlayer2', 'Identity')
            except:
                # Fallback for identity, with special handling for browsers
                name_lower = player_name.lower()
                if 'chromium' in name_lower:
                    identity = 'Chromium'
                elif 'google-chrome' in name_lower:
                    identity = 'Google Chrome'
                else:
                    identity = player_name.split('.')[-1].title()
            
            return {
                'metadata': metadata,
                'playback_status': playback_status,
                'player_identity': identity,
                'player_name': player_name
            }
        except:
            return None
    
    def format_time(self, seconds):
        if seconds <= 0:
            return "0:00"
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes}:{seconds:02d}"
    
    def get_music_icon(self, player_name):
        player_icons = {
            'spotify': 'spotify',
            'vlc': 'vlc',
            'rhythmbox': 'rhythmbox',
            'clementine': 'clementine',
            'audacious': 'audacious',
            'mpv': 'mpv',
            'chromium': 'chromium',
            'google-chrome': 'google-chrome'
        }
        
        # Handle browsers which may have dynamic instance names
        name_lower = player_name.lower()
        if 'chromium' in name_lower:
            return player_icons.get('chromium', 'media-playback-start')
        if 'google-chrome' in name_lower:
             return player_icons.get('google-chrome', 'media-playback-start')

        return player_icons.get(player_name.split('.')[-1].lower(), 'media-playback-start')
    
    def show_track_notification(self, player_info):
        metadata = player_info['metadata']
        
        title = str(metadata.get('xesam:title', 'Unknown Track'))
        artist = ', '.join([str(a) for a in metadata.get('xesam:artist', ['Unknown Artist'])])
        album = str(metadata.get('xesam:album', 'Unknown Album'))
        player = player_info['player_identity']
        
        notification_title = f"🎵 Now Playing • {player}"
        
        message_parts = [f"<b>{title}</b>"]
        if artist != 'Unknown Artist':
            message_parts.append(f"by {artist}")
        if album != 'Unknown Album':
            message_parts.append(f"from <i>{album}</i>")
        
        length = int(metadata.get('mpris:length', 0)) / 1000000
        if length > 0:
            duration = self.format_time(length)
            message_parts.append(f"[{duration}]")
        
        message = '\n'.join(message_parts)
        
        # Get icon
        icon = self.get_music_icon(player_info['player_name'])
        art_url = str(metadata.get('mpris:artUrl', ''))
        album_art = self.get_album_art_path(art_url)
        if album_art:
            icon = album_art
        
        self.send_notification(notification_title, message, icon)
    
    def handle_player_change(self, player_name):
        player_info = self.get_player_info(player_name)
        if not player_info:
            return
        
        metadata = player_info['metadata']
        playback_status = player_info['playback_status']
        
        # Only notify on new tracks that are playing
        if playback_status == 'Playing':
            track_signature = self.get_track_signature(metadata)
            
            # Only show notification if it's a genuinely new track
            if track_signature != self.current_track_signature:
                self.current_track_signature = track_signature
                self.show_track_notification(player_info)
        
        self.last_playback_status = playback_status
    
    def properties_changed(self, interface, changed, invalidated, path=None, sender=None):
        if interface != 'org.mpris.MediaPlayer2.Player':
            return
        
        # Only handle metadata or playback status changes
        if 'Metadata' in changed or 'PlaybackStatus' in changed:
            self.handle_player_change(sender)
    
    def find_playing_track(self):
        """Find currently playing track on startup"""
        try:
            names = self.bus.list_names()
            players = [n for n in names if n.startswith('org.mpris.MediaPlayer2.')]
            
            for player in players:
                player_info = self.get_player_info(player)
                if player_info and player_info['playback_status'] == 'Playing':
                    metadata = player_info['metadata']
                    if metadata.get('xesam:title'):
                        self.current_track_signature = self.get_track_signature(metadata)
                        self.show_track_notification(player_info)
                        break
        except:
            pass
        return False
    
    def run(self):
        signal.signal(signal.SIGTERM, self.handle_exit)
        signal.signal(signal.SIGINT, self.handle_exit)
        
        self.bus.add_signal_receiver(
            self.properties_changed,
            signal_name='PropertiesChanged',
            dbus_interface='org.freedesktop.DBus.Properties',
            sender_keyword='sender'
        )
        
        # Show current playing track once on startup
        GLib.timeout_add(1000, self.find_playing_track)
        
        self.loop.run()


if __name__ == "__main__":
    try:
        MusicPlayerMonitor().run()
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
