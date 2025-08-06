#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YouTube Transcript AI Summarizer - Secure Version
Downloads transcripts and creates AI-powered summaries with timestamped links
Now with encrypted API key storage!
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import re
import os
from datetime import datetime
import threading
import json
import time
import keyring

try:
    from youtube_transcript_api import YouTubeTranscriptApi
except ImportError:
    print("youtube-transcript-api not found. Please install it with:")
    print("pip install youtube-transcript-api")
    exit(1)

try:
    import openai
except ImportError:
    print("openai not found. Please install it with:")
    print("pip install openai")
    exit(1)


class YouTubeTranscriptAISummarizer:
    def __init__(self, root):
        self.root = root
        self.root.title("YouTube Transcript AI Summarizer")
        self.root.geometry("1000x700")
        self.root.resizable(True, True)
        
        # Constants for keyring
        self.KEYRING_SERVICE = "youtube_transcript_summarizer"
        self.KEYRING_USERNAME = "openai_api_key"
        
        # Variables
        self.transcript_text = ""
        self.video_id = ""
        self.video_url = ""
        self.transcript_data = []
        self.ai_summary = ""
        self.openai_client = None
        
        self.setup_ui()
        
        # Try to load saved API key
        self.load_saved_api_key()
        
    def setup_ui(self):
        """Create the GUI layout"""
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Tab 1: Main transcript fetcher
        self.main_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.main_frame, text="Transcript & Summary")
        
        # Tab 2: Settings
        self.settings_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.settings_frame, text="Settings")
        
        self.setup_main_tab()
        self.setup_settings_tab()
        
    def setup_main_tab(self):
        """Setup the main transcript and summary tab"""
        # Configure grid weights
        self.main_frame.columnconfigure(0, weight=1)
        self.main_frame.columnconfigure(1, weight=1)
        self.main_frame.rowconfigure(5, weight=1)
        
        # URL input section
        ttk.Label(self.main_frame, text="YouTube URL:", font=("Arial", 12, "bold")).grid(
            row=0, column=0, columnspan=2, sticky=tk.W, padx=10, pady=(10, 5)
        )
        
        self.url_var = tk.StringVar()
        self.url_entry = ttk.Entry(self.main_frame, textvariable=self.url_var, font=("Arial", 11))
        self.url_entry.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), padx=10, pady=(0, 10))
        self.url_entry.bind("<Return>", lambda e: self.fetch_transcript())
        
        # Buttons frame
        buttons_frame = ttk.Frame(self.main_frame)
        buttons_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), padx=10, pady=(0, 10))
        buttons_frame.columnconfigure(0, weight=1)
        buttons_frame.columnconfigure(1, weight=1)
        buttons_frame.columnconfigure(2, weight=1)
        buttons_frame.columnconfigure(3, weight=1)
        
        self.fetch_btn = ttk.Button(
            buttons_frame, text="Fetch Transcript", command=self.fetch_transcript
        )
        self.fetch_btn.grid(row=0, column=0, padx=(0, 5), sticky=(tk.W, tk.E))
        
        self.summarize_btn = ttk.Button(
            buttons_frame, text="AI Summary", command=self.create_ai_summary, state="disabled"
        )
        self.summarize_btn.grid(row=0, column=1, padx=5, sticky=(tk.W, tk.E))
        
        self.save_btn = ttk.Button(
            buttons_frame, text="Save Files", command=self.save_files, state="disabled"
        )
        self.save_btn.grid(row=0, column=2, padx=5, sticky=(tk.W, tk.E))
        
        self.clear_btn = ttk.Button(
            buttons_frame, text="Clear All", command=self.clear_all
        )
        self.clear_btn.grid(row=0, column=3, padx=(5, 0), sticky=(tk.W, tk.E))
        
        # Progress bar
        self.progress = ttk.Progressbar(self.main_frame, mode='indeterminate')
        self.progress.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), padx=10, pady=(0, 10))
        
        # Status label
        self.status_var = tk.StringVar(value="Ready - Enter YouTube URL above")
        self.status_label = ttk.Label(self.main_frame, textvariable=self.status_var, foreground="blue")
        self.status_label.grid(row=4, column=0, columnspan=2, sticky=tk.W, padx=10, pady=(0, 10))
        
        # Create paned window for transcript and summary
        self.paned_window = ttk.PanedWindow(self.main_frame, orient=tk.HORIZONTAL)
        self.paned_window.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), padx=10, pady=(0, 10))
        
        # Transcript display (left side)
        transcript_frame = ttk.LabelFrame(self.paned_window, text="Raw Transcript", padding="5")
        self.paned_window.add(transcript_frame, weight=1)
        
        self.transcript_display = scrolledtext.ScrolledText(
            transcript_frame,
            wrap=tk.WORD,
            width=40,
            height=20,
            font=("Arial", 10)
        )
        self.transcript_display.pack(fill=tk.BOTH, expand=True)
        
        # Summary display (right side)
        summary_frame = ttk.LabelFrame(self.paned_window, text="AI Summary with Timestamps", padding="5")
        self.paned_window.add(summary_frame, weight=1)
        
        self.summary_display = scrolledtext.ScrolledText(
            summary_frame,
            wrap=tk.WORD,
            width=40,
            height=20,
            font=("Arial", 10)
        )
        self.summary_display.pack(fill=tk.BOTH, expand=True)
        
        # Example URL label
        example_label = ttk.Label(
            self.main_frame,
            text="Example: https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            foreground="gray",
            font=("Arial", 9)
        )
        example_label.grid(row=6, column=0, columnspan=2, sticky=tk.W, padx=10, pady=(5, 10))
        
    def setup_settings_tab(self):
        """Setup the settings tab"""
        settings_main = ttk.Frame(self.settings_frame, padding="20")
        settings_main.pack(fill=tk.BOTH, expand=True)
        
        # OpenAI API Key section
        api_frame = ttk.LabelFrame(settings_main, text="OpenAI Configuration", padding="10")
        api_frame.pack(fill=tk.X, pady=(0, 20))
        
        ttk.Label(api_frame, text="OpenAI API Key:", font=("Arial", 11, "bold")).pack(anchor=tk.W)
        
        # Key entry frame
        key_frame = ttk.Frame(api_frame)
        key_frame.pack(fill=tk.X, pady=(5, 10))
        
        self.api_key_var = tk.StringVar()
        self.api_key_entry = ttk.Entry(
            key_frame, 
            textvariable=self.api_key_var, 
            show="*",  # Hide the key
            font=("Arial", 10)
        )
        self.api_key_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        # Button frame for API key actions
        key_buttons_frame = ttk.Frame(key_frame)
        key_buttons_frame.pack(side=tk.RIGHT)
        
        self.test_key_btn = ttk.Button(
            key_buttons_frame, 
            text="Test Key", 
            command=self.test_api_key
        )
        self.test_key_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # Save key checkbox
        self.save_key_var = tk.BooleanVar(value=False)
        self.save_key_checkbox = ttk.Checkbutton(
            api_frame,
            text="Save API key encrypted (auto-load on startup)",
            variable=self.save_key_var,
            command=self.toggle_save_key
        )
        self.save_key_checkbox.pack(anchor=tk.W, pady=(5, 5))
        
        # Key status label
        self.key_status_var = tk.StringVar(value="No saved key found")
        self.key_status_label = ttk.Label(
            api_frame,
            textvariable=self.key_status_var,
            foreground="gray",
            font=("Arial", 9)
        )
        self.key_status_label.pack(anchor=tk.W)
        
        # Clear saved key button
        self.clear_key_btn = ttk.Button(
            api_frame,
            text="Clear Saved Key",
            command=self.clear_saved_key,
            state="disabled"
        )
        self.clear_key_btn.pack(anchor=tk.W, pady=(5, 0))
        
        # Instructions
        instructions = ttk.Label(
            api_frame,
            text="1. Go to https://platform.openai.com/api-keys\n"
                 "2. Create a new secret key\n"
                 "3. Paste it above (it will be hidden)\n"
                 "4. Click 'Test Key' to verify it works\n"
                 "5. Check 'Save API key' to remember it",
            font=("Arial", 9),
            foreground="gray"
        )
        instructions.pack(anchor=tk.W, pady=(10, 0))
        
        # Model selection
        model_frame = ttk.LabelFrame(settings_main, text="AI Model Selection", padding="10")
        model_frame.pack(fill=tk.X, pady=(0, 20))
        
        self.model_var = tk.StringVar(value="gpt-4o-mini")
        
        models = [
            ("GPT-4o-mini (Recommended - Fast & Cheap)", "gpt-4o-mini"),
            ("GPT-4o (More Capable - Higher Cost)", "gpt-4o"),
            ("GPT-3.5-turbo (Older - Cheaper)", "gpt-3.5-turbo")
        ]
        
        for text, value in models:
            ttk.Radiobutton(
                model_frame, 
                text=text, 
                variable=self.model_var, 
                value=value
            ).pack(anchor=tk.W, pady=2)
        
        # Summary settings
        summary_frame = ttk.LabelFrame(settings_main, text="Summary Settings", padding="10")
        summary_frame.pack(fill=tk.X)
        
        ttk.Label(summary_frame, text="Summary Style:").pack(anchor=tk.W)
        
        self.summary_style_var = tk.StringVar(value="detailed")
        
        styles = [
            ("Detailed with timestamps", "detailed"),
            ("Brief overview", "brief"),
            ("Key points only", "key_points")
        ]
        
        for text, value in styles:
            ttk.Radiobutton(
                summary_frame,
                text=text,
                variable=self.summary_style_var,
                value=value
            ).pack(anchor=tk.W, pady=2)
    
    def load_saved_api_key(self):
        """Try to load saved API key from keyring"""
        try:
            saved_key = keyring.get_password(self.KEYRING_SERVICE, self.KEYRING_USERNAME)
            if saved_key:
                self.api_key_var.set(saved_key)
                self.save_key_var.set(True)
                self.key_status_var.set("✅ API key loaded from secure storage")
                self.key_status_label.config(foreground="green")
                self.clear_key_btn.config(state="normal")
                
                # Initialize OpenAI client with saved key
                self.openai_client = openai.OpenAI(api_key=saved_key)
                
                # Update main status
                self.status_var.set("Ready - API key loaded from secure storage")
        except Exception as e:
            # Keyring not available or key not found
            self.key_status_var.set("No saved key found")
            self.key_status_label.config(foreground="gray")
    
    def toggle_save_key(self):
        """Handle save key checkbox toggle"""
        if self.save_key_var.get():
            # User wants to save the key
            api_key = self.api_key_var.get().strip()
            if not api_key:
                messagebox.showerror("Error", "Please enter an API key first")
                self.save_key_var.set(False)
                return
            
            # Test the key first
            if self.test_api_key_silent():
                # Save to keyring
                try:
                    keyring.set_password(self.KEYRING_SERVICE, self.KEYRING_USERNAME, api_key)
                    self.key_status_var.set("✅ API key saved to secure storage")
                    self.key_status_label.config(foreground="green")
                    self.clear_key_btn.config(state="normal")
                    messagebox.showinfo("Success", "API key saved securely! It will auto-load next time.")
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to save key: {str(e)}")
                    self.save_key_var.set(False)
            else:
                self.save_key_var.set(False)
        else:
            # User unchecked - just update status, don't delete
            self.key_status_var.set("Key not being saved")
            self.key_status_label.config(foreground="gray")
    
    def clear_saved_key(self):
        """Clear saved API key from keyring"""
        try:
            keyring.delete_password(self.KEYRING_SERVICE, self.KEYRING_USERNAME)
            self.key_status_var.set("Saved key cleared")
            self.key_status_label.config(foreground="gray")
            self.clear_key_btn.config(state="disabled")
            self.save_key_var.set(False)
            messagebox.showinfo("Success", "Saved API key has been cleared from secure storage.")
        except Exception as e:
            # Key might not exist, that's okay
            self.key_status_var.set("No saved key found")
            self.key_status_label.config(foreground="gray")
            self.clear_key_btn.config(state="disabled")
    
    def test_api_key_silent(self):
        """Test API key without showing dialog - returns True if valid"""
        api_key = self.api_key_var.get().strip()
        if not api_key:
            return False
        
        try:
            client = openai.OpenAI(api_key=api_key)
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": "Hello, respond with just 'OK'"}],
                max_tokens=5
            )
            
            if response.choices[0].message.content:
                self.openai_client = client
                return True
        except:
            return False
        
        return False
    
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
    
    def test_api_key(self):
        """Test if the OpenAI API key works"""
        api_key = self.api_key_var.get().strip()
        if not api_key:
            messagebox.showerror("Error", "Please enter your OpenAI API key")
            return
        
        try:
            client = openai.OpenAI(api_key=api_key)
            
            # Test with a simple completion
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": "Hello, respond with just 'API key works!'"}],
                max_tokens=10
            )
            
            if response.choices[0].message.content:
                self.openai_client = client
                messagebox.showinfo("Success", "✅ API key is valid and working!")
                self.status_var.set("OpenAI API key configured successfully")
            else:
                messagebox.showerror("Error", "❌ Invalid response from OpenAI")
                
        except Exception as e:
            messagebox.showerror("Error", f"❌ API key test failed:\n{str(e)}")
    
    def fetch_transcript(self):
        """Fetch transcript from YouTube video"""
        url = self.url_var.get().strip()
        if not url:
            messagebox.showerror("Error", "Please enter a YouTube URL")
            return
        
        video_id = self.extract_video_id(url)
        if not video_id:
            messagebox.showerror("Error", "Invalid YouTube URL")
            return
        
        self.video_id = video_id
        self.video_url = url
        
        # Start fetching in a separate thread
        thread = threading.Thread(target=self._fetch_transcript_thread)
        thread.daemon = True
        thread.start()
    
    def _fetch_transcript_thread(self):
        """Thread function to fetch transcript"""
        try:
            self.root.after(0, self._update_ui_fetching)
            
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
                    
                except UnicodeEncodeError:
                    continue
            
            self.transcript_text = ' '.join(transcript_lines)
            
            if not self.transcript_text:
                raise Exception("No transcript text could be extracted.")
            
            self.root.after(0, self._update_ui_success)
            
        except Exception as e:
            error_msg = self._format_error_message(str(e))
            self.root.after(0, lambda: self._update_ui_error(error_msg))
    
    def create_ai_summary(self):
        """Create AI summary of the transcript"""
        if not self.transcript_text:
            messagebox.showerror("Error", "No transcript available to summarize")
            return
        
        if not self.openai_client:
            api_key = self.api_key_var.get().strip()
            if not api_key:
                messagebox.showerror("Error", "Please enter your OpenAI API key in Settings tab")
                return
            
            try:
                self.openai_client = openai.OpenAI(api_key=api_key)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to initialize OpenAI client:\n{str(e)}")
                return
        
        # Start summarization in a separate thread
        thread = threading.Thread(target=self._create_summary_thread)
        thread.daemon = True
        thread.start()
    
    def _create_summary_thread(self):
        """Thread function to create AI summary"""
        try:
            self.root.after(0, self._update_ui_summarizing)
            
            # Create the prompt based on style
            style = self.summary_style_var.get()
            
            if style == "detailed":
                prompt = self._get_detailed_prompt()
            elif style == "brief":
                prompt = self._get_brief_prompt()
            else:  # key_points
                prompt = self._get_key_points_prompt()
            
            # Get AI response
            response = self.openai_client.chat.completions.create(
                model=self.model_var.get(),
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
            
            self.root.after(0, self._update_ui_summary_complete)
            
        except Exception as e:
            error_msg = f"AI summarization failed:\n{str(e)}"
            self.root.after(0, lambda: self._update_ui_error(error_msg))
    
    def _get_detailed_prompt(self):
        """Get detailed summary prompt"""
        return f"""
Please create a detailed structured summary of this YouTube video transcript. 

TRANSCRIPT:
{self.transcript_text}

Please format your response as:

# Video Summary

## Section 1: [Title] (START_TIME - END_TIME)
- Key point 1
- Key point 2  
- Key point 3

## Section 2: [Title] (START_TIME - END_TIME) 
- Key point 1
- Key point 2
- Key point 3

Continue this pattern for the entire transcript. 

For timestamps, estimate reasonable sections (like every 2-5 minutes) and use format like "2:30 - 5:45" based on the content flow. Make sure each section has a clear, descriptive title and 2-4 bullet points summarizing the key information discussed in that timeframe.
"""
    
    def _get_brief_prompt(self):
        """Get brief summary prompt"""
        return f"""
Create a brief overview summary of this YouTube video transcript in 3-5 sections:

TRANSCRIPT:
{self.transcript_text}

Format as:
# Brief Video Summary

## Introduction (0:00 - X:XX)
- Brief summary

## Main Content (X:XX - X:XX)  
- Brief summary

## Conclusion (X:XX - END)
- Brief summary

Keep each section to 1-2 bullet points maximum.
"""
    
    def _get_key_points_prompt(self):
        """Get key points only prompt"""
        return f"""
Extract only the most important key points from this YouTube video transcript:

TRANSCRIPT:
{self.transcript_text}

Format as:
# Key Points Summary

• Point 1 (around X:XX)
• Point 2 (around X:XX)
• Point 3 (around X:XX)
• Point 4 (around X:XX)
• Point 5 (around X:XX)

List 5-10 most important points with approximate timestamps.
"""
    
    def _add_timestamped_urls(self, summary_text):
        """Add clickable URLs with timestamps to the summary"""
        # Pattern to find timestamps like "2:30", "1:05:30", etc.
        timestamp_pattern = r'(\d{1,2}:\d{2}(?::\d{2})?)'
        
        def replace_timestamp(match):
            timestamp = match.group(1)
            seconds = self._timestamp_to_seconds(timestamp)
            url = f"{self.video_url}&t={seconds}s"
            return f"{timestamp}\n🔗 {url}"
        
        # Replace timestamps with URLs
        enhanced_summary = re.sub(timestamp_pattern, replace_timestamp, summary_text)
        
        return enhanced_summary
    
    def _timestamp_to_seconds(self, timestamp):
        """Convert timestamp like '2:30' or '1:05:30' to seconds"""
        parts = timestamp.split(':')
        
        if len(parts) == 2:  # MM:SS
            minutes, seconds = map(int, parts)
            return minutes * 60 + seconds
        elif len(parts) == 3:  # HH:MM:SS
            hours, minutes, seconds = map(int, parts)
            return hours * 3600 + minutes * 60 + seconds
        else:
            return 0
    
    def _format_error_message(self, error):
        """Format error message for better user understanding"""
        if "No transcript" in error or "CouldNotRetrieveTranscript" in error:
            return ("This video doesn't have transcripts available.\n\n"
                   "Try a different video that has captions enabled.")
        elif "VideoUnavailable" in error:
            return "This video is unavailable or private."
        else:
            return f"Error: {error}"
    
    def _update_ui_fetching(self):
        """Update UI during transcript fetching"""
        self.status_var.set("Fetching transcript...")
        self.progress.start()
        self.fetch_btn.config(state="disabled")
        self.summarize_btn.config(state="disabled")
        self.save_btn.config(state="disabled")
    
    def _update_ui_summarizing(self):
        """Update UI during AI summarization"""
        self.status_var.set("Creating AI summary... (this may take 10-30 seconds)")
        self.progress.start()
        self.summarize_btn.config(state="disabled")
    
    def _update_ui_success(self):
        """Update UI after successful transcript fetch"""
        self.progress.stop()
        self.status_var.set(f"Transcript fetched! ({len(self.transcript_text)} characters) - Ready for AI summary")
        
        self.transcript_display.delete(1.0, tk.END)
        self.transcript_display.insert(1.0, self.transcript_text)
        
        self.fetch_btn.config(state="normal")
        self.summarize_btn.config(state="normal")
        self.save_btn.config(state="normal")
    
    def _update_ui_summary_complete(self):
        """Update UI after successful AI summary"""
        self.progress.stop()
        self.status_var.set("AI summary complete! Click links to jump to video sections")
        
        self.summary_display.delete(1.0, tk.END)
        self.summary_display.insert(1.0, self.ai_summary)
        
        self.summarize_btn.config(state="normal")
    
    def _update_ui_error(self, error_msg):
        """Update UI after error"""
        self.progress.stop()
        self.status_var.set("Error occurred")
        self.fetch_btn.config(state="normal")
        self.summarize_btn.config(state="normal")
        messagebox.showerror("Error", error_msg)
    
    def save_files(self):
        """Save transcript and summary to files"""
        if not self.transcript_data:
            messagebox.showwarning("Warning", "No content to save")
            return
        
        # Ask for directory
        directory = filedialog.askdirectory(title="Select folder to save files")
        if not directory:
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_filename = f"youtube_{self.video_id}_{timestamp}"
        
        try:
            # Save original transcript
            transcript_file = os.path.join(directory, f"{base_filename}_transcript.txt")
            with open(transcript_file, 'w', encoding='utf-8') as f:
                f.write(f"YouTube Video: {self.video_url}\n")
                f.write(f"Transcript extracted on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                f.write(self.transcript_text)
            
            # Save AI summary if available
            if self.ai_summary:
                summary_file = os.path.join(directory, f"{base_filename}_ai_summary.md")
                with open(summary_file, 'w', encoding='utf-8') as f:
                    f.write(f"# AI Summary\n\n")
                    f.write(f"**Video:** {self.video_url}\n")
                    f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"**Model:** {self.model_var.get()}\n\n")
                    f.write(self.ai_summary)
            
            # Save JSON data
            json_file = os.path.join(directory, f"{base_filename}_data.json")
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'video_url': self.video_url,
                    'video_id': self.video_id,
                    'transcript_data': self.transcript_data,
                    'ai_summary': self.ai_summary,
                    'generated_at': datetime.now().isoformat()
                }, f, indent=2, ensure_ascii=False)
            
            files_saved = [os.path.basename(transcript_file), os.path.basename(json_file)]
            if self.ai_summary:
                files_saved.append(os.path.basename(summary_file))
            
            messagebox.showinfo("Success", f"Files saved successfully:\n" + "\n".join(files_saved))
            self.status_var.set(f"Files saved to: {directory}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save files:\n{str(e)}")
    
    def clear_all(self):
        """Clear all content"""
        self.url_var.set("")
        self.transcript_display.delete(1.0, tk.END)
        self.summary_display.delete(1.0, tk.END)
        self.transcript_text = ""
        self.transcript_data = []
        self.ai_summary = ""
        self.video_id = ""
        self.video_url = ""
        self.status_var.set("Ready - Enter YouTube URL above")
        self.save_btn.config(state="disabled")
        self.summarize_btn.config(state="disabled")


def main():
    """Main function"""
    root = tk.Tk()
    app = YouTubeTranscriptAISummarizer(root)
    root.mainloop()


if __name__ == "__main__":
    main()