#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YouTube Transcript AI Summarizer - Mobile Version
Built with Kivy/KivyMD for Android deployment
Keyring removed - uses file-based storage only
"""

__version__ = "1.0"

import os
import re
import json
import threading
from datetime import datetime

# Kivy imports
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.clock import Clock
from kivy.properties import StringProperty, BooleanProperty
from kivy.utils import platform

# KivyMD imports
from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.textfield import MDTextField
from kivymd.uix.button import MDRaisedButton, MDFlatButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.progressbar import MDProgressBar
from kivymd.uix.tab import MDTabs, MDTabsBase
from kivymd.uix.card import MDCard
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.selectioncontrol import MDCheckbox
from kivymd.uix.list import OneLineListItem, TwoLineListItem
from kivymd.uix.scrollview import MDScrollView
from kivymd.toast import toast

# API imports
try:
    from youtube_transcript_api import YouTubeTranscriptApi
except ImportError:
    print("youtube-transcript-api not found")

try:
    import openai
except ImportError:
    print("openai not found")

# Android-specific imports
if platform == 'android':
    from android.permissions import request_permissions, Permission
    from android.storage import primary_external_storage_path
    
    # Request necessary permissions
    request_permissions([
        Permission.INTERNET,
        Permission.WRITE_EXTERNAL_STORAGE,
        Permission.READ_EXTERNAL_STORAGE
    ])


class TranscriptTab(MDBoxLayout, MDTabsBase):
    """Tab for transcript display"""
    pass


class SummaryTab(MDBoxLayout, MDTabsBase):
    """Tab for AI summary display"""
    pass


class MainScreen(MDScreen):
    """Main screen with transcript and summary functionality"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app = MDApp.get_running_app()
        self.transcript_text = ""
        self.ai_summary = ""
        self.video_id = ""
        self.video_url = ""
        self.transcript_data = []
        
    def fetch_transcript(self):
        """Fetch transcript from YouTube video"""
        url = self.ids.url_input.text.strip()
        if not url:
            self.show_error("Please enter a YouTube URL")
            return
        
        video_id = self.extract_video_id(url)
        if not video_id:
            self.show_error("Invalid YouTube URL")
            return
        
        self.video_id = video_id
        self.video_url = url
        
        # Show progress
        self.ids.progress_bar.opacity = 1
        self.ids.status_label.text = "Fetching transcript..."
        
        # Start in thread
        threading.Thread(target=self._fetch_transcript_thread, daemon=True).start()
    
    def _fetch_transcript_thread(self):
        """Thread function to fetch transcript"""
        try:
            api = YouTubeTranscriptApi()
            transcript = api.fetch(self.video_id)
            
            self.transcript_data = []
            transcript_lines = []
            
            for snippet in transcript:
                try:
                    text = snippet.text
                    start = snippet.start
                    duration = snippet.duration
                    
                    self.transcript_data.append({
                        'text': text,
                        'start': start,
                        'duration': duration
                    })
                    
                    transcript_lines.append(text)
                    
                except (UnicodeEncodeError, AttributeError):
                    continue
            
            self.transcript_text = ' '.join(transcript_lines)
            
            if not self.transcript_text:
                raise Exception("No transcript text could be extracted.")
            
            # Update UI on main thread
            Clock.schedule_once(lambda dt: self._update_ui_success())
            
        except Exception as e:
            error_msg = str(e)
            Clock.schedule_once(lambda dt: self._update_ui_error(error_msg))
    
    def _update_ui_success(self):
        """Update UI after successful fetch"""
        self.ids.progress_bar.opacity = 0
        self.ids.status_label.text = f"Transcript fetched! ({len(self.transcript_text)} chars)"
        self.ids.transcript_text.text = self.transcript_text[:5000] + "..." if len(self.transcript_text) > 5000 else self.transcript_text
        self.ids.summarize_btn.disabled = False
        self.ids.save_btn.disabled = False
    
    def _update_ui_error(self, error_msg):
        """Update UI after error"""
        self.ids.progress_bar.opacity = 0
        self.ids.status_label.text = "Error occurred"
        self.show_error(f"Failed to fetch transcript: {error_msg}")
    
    def create_ai_summary(self):
        """Create AI summary of the transcript"""
        if not self.transcript_text:
            self.show_error("No transcript available to summarize")
            return
        
        if not self.app.openai_client:
            self.show_error("Please configure your OpenAI API key in Settings")
            return
        
        # Show progress
        self.ids.progress_bar.opacity = 1
        self.ids.status_label.text = "Creating AI summary..."
        
        # Start in thread
        threading.Thread(target=self._create_summary_thread, daemon=True).start()
    
    def _create_summary_thread(self):
        """Thread function to create AI summary"""
        try:
            # Create prompt based on selected style
            style = self.app.summary_style
            
            if style == "detailed":
                prompt = self._get_detailed_prompt()
            elif style == "brief":
                prompt = self._get_brief_prompt()
            else:
                prompt = self._get_key_points_prompt()
            
            # Get AI response
            response = self.app.openai_client.chat.completions.create(
                model=self.app.ai_model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that creates structured summaries of YouTube video transcripts."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=2000,
                temperature=0.3
            )
            
            summary_text = response.choices[0].message.content
            
            # Add timestamped URLs
            self.ai_summary = self._add_timestamped_urls(summary_text)
            
            # Update UI on main thread
            Clock.schedule_once(lambda dt: self._update_summary_ui())
            
        except Exception as e:
            error_msg = str(e)
            Clock.schedule_once(lambda dt: self._update_ui_error(f"AI summarization failed: {error_msg}"))
    
    def _update_summary_ui(self):
        """Update UI with AI summary"""
        self.ids.progress_bar.opacity = 0
        self.ids.status_label.text = "AI summary complete!"
        self.ids.summary_text.text = self.ai_summary
        
        # Switch to summary tab
        self.ids.tabs.switch_tab('Summary')
    
    def _get_detailed_prompt(self):
        """Get detailed summary prompt"""
        # Limit transcript length for API
        truncated_text = self.transcript_text[:8000] if len(self.transcript_text) > 8000 else self.transcript_text
        
        return f"""
Please create a detailed structured summary of this YouTube video transcript. 

TRANSCRIPT:
{truncated_text}

Please format your response as:

# Video Summary

## Section 1: [Title] (START_TIME - END_TIME)
- Key point 1
- Key point 2  

## Section 2: [Title] (START_TIME - END_TIME) 
- Key point 1
- Key point 2

Continue this pattern. Use timestamps like "2:30 - 5:45".
"""
    
    def _get_brief_prompt(self):
        """Get brief summary prompt"""
        truncated_text = self.transcript_text[:8000] if len(self.transcript_text) > 8000 else self.transcript_text
        
        return f"""
Create a brief overview summary of this YouTube video transcript in 3-5 sections:

TRANSCRIPT:
{truncated_text}

Format as:
# Brief Video Summary

## Introduction (0:00 - X:XX)
- Brief summary

## Main Content (X:XX - X:XX)  
- Brief summary

Keep each section to 1-2 bullet points.
"""
    
    def _get_key_points_prompt(self):
        """Get key points only prompt"""
        truncated_text = self.transcript_text[:8000] if len(self.transcript_text) > 8000 else self.transcript_text
        
        return f"""
Extract the most important key points from this YouTube video transcript:

TRANSCRIPT:
{truncated_text}

Format as:
# Key Points Summary

• Point 1 (around X:XX)
• Point 2 (around X:XX)
• Point 3 (around X:XX)

List 5-8 most important points with timestamps.
"""
    
    def _add_timestamped_urls(self, summary_text):
        """Add clickable URLs with timestamps to the summary"""
        timestamp_pattern = r'(\d{1,2}:\d{2}(?::\d{2})?)'
        
        def replace_timestamp(match):
            timestamp = match.group(1)
            seconds = self._timestamp_to_seconds(timestamp)
            url = f"{self.video_url}&t={seconds}s"
            return f"{timestamp}\n[color=0088FF][ref={url}]{url}[/ref][/color]"
        
        enhanced_summary = re.sub(timestamp_pattern, replace_timestamp, summary_text)
        return enhanced_summary
    
    def _timestamp_to_seconds(self, timestamp):
        """Convert timestamp to seconds"""
        parts = timestamp.split(':')
        
        if len(parts) == 2:
            minutes, seconds = map(int, parts)
            return minutes * 60 + seconds
        elif len(parts) == 3:
            hours, minutes, seconds = map(int, parts)
            return hours * 3600 + minutes * 60 + seconds
        else:
            return 0
    
    def extract_video_id(self, url):
        """Extract video ID from YouTube URL"""
        patterns = [
            r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
            r'(?:embed\/)([0-9A-Za-z_-]{11})',
            r'(?:youtu\.be\/)([0-9A-Za-z_-]{11})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None
    
    def save_files(self):
        """Save transcript and summary"""
        if not self.transcript_data:
            self.show_error("No content to save")
            return
        
        # Get storage directory
        if platform == 'android':
            try:
                directory = primary_external_storage_path()
                directory = os.path.join(directory, "YouTubeTranscripts")
                os.makedirs(directory, exist_ok=True)
            except:
                directory = "/sdcard/YouTubeTranscripts"
                try:
                    os.makedirs(directory, exist_ok=True)
                except:
                    directory = "/sdcard"
        else:
            directory = os.path.expanduser("~/Documents")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_filename = f"youtube_{self.video_id}_{timestamp}"
        
        try:
            # Save files
            transcript_file = os.path.join(directory, f"{base_filename}_transcript.txt")
            with open(transcript_file, 'w', encoding='utf-8') as f:
                f.write(f"YouTube Video: {self.video_url}\n")
                f.write(f"Transcript extracted on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                f.write(self.transcript_text)
            
            if self.ai_summary:
                summary_file = os.path.join(directory, f"{base_filename}_summary.md")
                with open(summary_file, 'w', encoding='utf-8') as f:
                    f.write(f"# AI Summary\n\n")
                    f.write(f"**Video:** {self.video_url}\n")
                    f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                    # Clean up markup
                    clean_summary = self.ai_summary.replace('[color=0088FF][ref=', '').replace('][/ref][/color]', '')
                    f.write(clean_summary)
            
            toast(f"Files saved to {directory}")
            
        except Exception as e:
            self.show_error(f"Failed to save files: {str(e)}")
    
    def show_error(self, message):
        """Show error dialog"""
        dialog = MDDialog(
            title="Error",
            text=message,
            size_hint=(0.8, None),
            height="200dp",
            buttons=[
                MDFlatButton(
                    text="OK",
                    on_release=lambda x: dialog.dismiss()
                )
            ]
        )
        dialog.open()
    
    def clear_all(self):
        """Clear all content"""
        self.ids.url_input.text = ""
        self.ids.transcript_text.text = ""
        self.ids.summary_text.text = ""
        self.transcript_text = ""
        self.transcript_data = []
        self.ai_summary = ""
        self.video_id = ""
        self.video_url = ""
        self.ids.status_label.text = "Ready"
        self.ids.summarize_btn.disabled = True
        self.ids.save_btn.disabled = True


class SettingsScreen(MDScreen):
    """Settings screen for API configuration"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app = MDApp.get_running_app()
        
    def on_enter(self):
        """Called when entering the screen"""
        # Load saved key if exists
        if self.app.api_key:
            self.ids.api_key_input.text = self.app.api_key
            self.ids.save_key_checkbox.active = self.app.save_key_enabled
    
    def test_api_key(self):
        """Test the API key"""
        api_key = self.ids.api_key_input.text.strip()
        if not api_key:
            self.show_error("Please enter your OpenAI API key")
            return
        
        try:
            client = openai.OpenAI(api_key=api_key)
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": "Hello, respond with just 'OK'"}],
                max_tokens=5
            )
            
            if response.choices[0].message.content:
                self.app.openai_client = client
                self.app.api_key = api_key
                toast("✅ API key is valid!")
        except Exception as e:
            self.show_error(f"API key test failed: {str(e)}")
    
    def toggle_save_key(self, checkbox):
        """Handle save key toggle - file storage only, no keyring"""
        if checkbox.active:
            api_key = self.ids.api_key_input.text.strip()
            if not api_key:
                self.show_error("Please enter an API key first")
                checkbox.active = False
                return
            
            # Use file storage for all platforms (no keyring)
            try:
                if platform == 'android':
                    config_dir = "/data/data/com.mine.youtubetranscript/files"
                    os.makedirs(config_dir, exist_ok=True)
                    config_file = os.path.join(config_dir, "api_key.txt")
                else:
                    # Desktop: use home directory
                    config_dir = os.path.expanduser("~/.youtube_transcript")
                    os.makedirs(config_dir, exist_ok=True)
                    config_file = os.path.join(config_dir, "api_key.txt")
                
                with open(config_file, 'w') as f:
                    f.write(api_key)
                
                self.app.save_key_enabled = True
                toast("API key saved!")
                
            except Exception as e:
                self.show_error(f"Failed to save key: {str(e)}")
                checkbox.active = False
        else:
            # Remove saved key
            try:
                if platform == 'android':
                    config_file = "/data/data/com.mine.youtubetranscript/files/api_key.txt"
                else:
                    config_file = os.path.expanduser("~/.youtube_transcript/api_key.txt")
                
                if os.path.exists(config_file):
                    os.remove(config_file)
                
                self.app.save_key_enabled = False
                toast("Saved key removed")
                
            except Exception as e:
                self.show_error(f"Failed to remove key: {str(e)}")
    
    def update_model(self, model):
        """Update selected AI model"""
        self.app.ai_model = model
        toast(f"Model changed to {model}")
    
    def update_style(self, style):
        """Update summary style"""
        self.app.summary_style = style
        toast(f"Summary style changed to {style}")
    
    def show_error(self, message):
        """Show error dialog"""
        dialog = MDDialog(
            title="Error",
            text=message,
            size_hint=(0.8, None),
            height="200dp",
            buttons=[
                MDFlatButton(
                    text="OK",
                    on_release=lambda x: dialog.dismiss()
                )
            ]
        )
        dialog.open()


class YouTubeTranscriptApp(MDApp):
    """Main application class"""
    
    # App properties
    api_key = StringProperty("")
    save_key_enabled = BooleanProperty(False)
    ai_model = StringProperty("gpt-4o-mini")
    summary_style = StringProperty("detailed")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.openai_client = None
        self.theme_cls.primary_palette = "Teal"
        self.theme_cls.theme_style = "Light"
        
    def build(self):
        """Build the app UI"""
        self.title = "YouTube AI Summarizer"
        
        # Load saved API key
        self.load_saved_key()
        
        # Create screen manager
        sm = ScreenManager()
        sm.add_widget(MainScreen(name='main'))
        sm.add_widget(SettingsScreen(name='settings'))
        
        return sm
    
    def load_saved_key(self):
        """Load saved API key from file storage only"""
        try:
            if platform == 'android':
                config_file = "/data/data/com.mine.youtubetranscript/files/api_key.txt"
            else:
                config_file = os.path.expanduser("~/.youtube_transcript/api_key.txt")
            
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    saved_key = f.read().strip()
                    if saved_key:
                        self.api_key = saved_key
                        self.save_key_enabled = True
                        self.openai_client = openai.OpenAI(api_key=saved_key)
                        toast("API key loaded")
        except Exception:
            pass
    
    def switch_screen(self, screen_name):
        """Switch to a different screen"""
        self.root.current = screen_name


if __name__ == "__main__":
    YouTubeTranscriptApp().run()
