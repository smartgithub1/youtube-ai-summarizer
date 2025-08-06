# 📱 YouTube AI Summarizer

**Transform YouTube videos into AI-powered summaries with timestamped links**

A cross-platform app (Desktop + Android) that downloads YouTube transcripts and creates intelligent summaries using OpenAI's GPT models, complete with clickable timestamp links to jump to specific video sections.

[![Build Android APK](https://github.com/yourusername/youtube-ai-summarizer/actions/workflows/build-android.yml/badge.svg)](https://github.com/yourusername/youtube-ai-summarizer/actions/workflows/build-android.yml)

## ✨ Features

### 🎯 **Core Functionality**
- **YouTube Transcript Extraction** - Downloads captions from any YouTube video
- **AI-Powered Summaries** - Uses GPT-4o-mini for intelligent content summarization  
- **Timestamped Links** - Click to jump directly to video sections
- **Multiple Summary Styles** - Detailed, Brief, or Key Points format
- **Secure API Storage** - Encrypted OpenAI key management

### 🖥️ **Desktop Version**
- **Rich GUI** with tkinter/Material Design
- **Side-by-side view** of transcript and summary
- **Export Options** - Save as Text, Markdown, SRT, or JSON
- **Windows Credential Manager** integration for secure key storage

### 📱 **Mobile Version** 
- **Material Design UI** built with Kivy/KivyMD
- **Touch-optimized interface** for phones and tablets
- **Android storage integration** - Saves to `/sdcard/YouTubeTranscripts/`
- **Secure key storage** with Android-specific methods
- **Portrait-optimized layout**

## 🚀 Quick Start

### Desktop App
```bash
# Install dependencies
pip install -r requirements.txt

# Run secure desktop version
python youtube_transcript_ai_summarizer_secure.py
```

### Mobile App (Test on Desktop)
```bash
# Install mobile dependencies
pip install kivy kivymd

# Run mobile version
python main.py
```

### Android APK
1. **Automatic Build**: Push to GitHub - APK built via GitHub Actions
2. **Download**: Get APK from the "Actions" tab
3. **Install**: Transfer to Android device and install

## 📋 Requirements

### Python Dependencies
```
youtube-transcript-api>=1.2.1
openai>=1.0.0
kivy>=2.0.0
kivymd>=1.0.0
keyring>=24.0.0
```

### API Keys
- **OpenAI API Key** - Get from [OpenAI Platform](https://platform.openai.com/api-keys)
- **Cost**: ~$0.01 per 10-minute video summary (very affordable!)

## 🛠️ Setup Instructions

### 1. **Clone Repository**
```bash
git clone https://github.com/yourusername/youtube-ai-summarizer.git
cd youtube-ai-summarizer
```

### 2. **Install Dependencies**
```bash
pip install -r requirements.txt
```

### 3. **Configure OpenAI API**
1. Get API key from [OpenAI Platform](https://platform.openai.com/api-keys)
2. Run the app and go to Settings
3. Enter your API key and click "Test Key"
4. Check "Save API key encrypted" to store securely

### 4. **Usage**
1. Paste any YouTube URL
2. Click "Fetch Transcript"
3. Click "AI Summary" 
4. View structured summary with clickable timestamps!

## 📱 Android Development

### Building APK

**Option 1: GitHub Actions (Recommended)**
1. Fork this repository
2. Push changes to trigger build
3. Download APK from Actions tab

**Option 2: Local Build (Linux/WSL)**
```bash
pip install buildozer
buildozer android debug
```

### APK Location
- **GitHub Actions**: `Artifacts` → `youtube-transcript-apk`
- **Local Build**: `./bin/youtubetranscript-1.0-debug.apk`

## 🎯 Example Output

```markdown
# Video Summary

## Introduction (0:00 - 2:30)
- Overview of the main topic
- Why this video matters
🔗 https://youtube.com/watch?v=VIDEO_ID&t=0s

## Key Concepts (2:30 - 8:45)
- Main concept explanation
- Important examples discussed
🔗 https://youtube.com/watch?v=VIDEO_ID&t=150s

## Conclusion (8:45 - 10:00)
- Key takeaways
- Next steps mentioned
🔗 https://youtube.com/watch?v=VIDEO_ID&t=525s
```

## 💰 Cost Analysis

Using GPT-4o-mini (recommended):
- **10-minute video**: ~$0.005 (half a cent)
- **30-minute video**: ~$0.015 (1.5 cents)  
- **60-minute video**: ~$0.03 (3 cents)

*Extremely affordable for the value provided!*

## 🔒 Security Features

- **Encrypted API Storage** - Uses system keyring/credential manager
- **No hardcoded keys** - User provides their own OpenAI key
- **Secure transmission** - All API calls use HTTPS
- **Local processing** - Transcripts processed locally before AI summarization

## 🏗️ Architecture

### Desktop (Python + tkinter)
```
├── GUI Layer (tkinter/ttk)
├── Business Logic (transcript fetching, AI processing)
├── Storage Layer (Windows Credential Manager)
└── API Layer (YouTube Transcript API, OpenAI API)
```

### Mobile (Python + Kivy)
```
├── UI Layer (KivyMD Material Design)
├── Business Logic (same as desktop)
├── Storage Layer (Android Keystore/file storage)
└── API Layer (same APIs with mobile optimizations)
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **YouTube Transcript API** - For transcript extraction
- **OpenAI** - For AI-powered summarization
- **Kivy/KivyMD** - For cross-platform mobile UI
- **GitHub Actions** - For automated Android builds

## 🐛 Troubleshooting

### Common Issues

**"No transcript found"**
- Video doesn't have captions enabled
- Try videos from major channels (they usually have captions)

**"API key failed"**
- Check OpenAI account has credits
- Verify key is copied correctly
- Ensure key has proper permissions

**Android build fails**
- Check GitHub Actions logs
- Ensure all files are committed to repository

### Support

- 📧 **Issues**: Use GitHub Issues for bug reports
- 💬 **Discussions**: Use GitHub Discussions for questions
- 📖 **Wiki**: Check the Wiki for detailed guides

---

**⭐ Star this repo if it helped you!** 

*Built with ❤️ for productivity and learning*