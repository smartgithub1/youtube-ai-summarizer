[app]

# App information
title = YouTube AI Summarizer
package.name = youtubetranscript
package.domain = com.mine.youtubetranscript

# Source code location
source.dir = .
source.include_exts = py,png,jpg,kv,atlas

# Version information
version = 1.0

# Requirements
requirements = python3,kivy,kivymd,youtube-transcript-api,openai,requests,urllib3,certifi,charset-normalizer,idna

# Permissions for Android
android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE

# Android specific
android.api = 30
android.minapi = 21
android.ndk = 23c
android.sdk = 30
android.accept_sdk_license = True
android.gradle_dependencies = 
p4a.bootstrap = sdl2
android.gradle_dependencies = com.android.support:support-v4:28.0.0
# Icons (optional)
#icon.filename = %(source.dir)s/icon.png

# Presplash (optional)
#presplash.filename = %(source.dir)s/presplash.png

# Orientation
orientation = portrait

[buildozer]

# Log level
log_level = 2

# Build directory
build_dir = ./.buildozer

# Bin directory  
bin_dir = ./bin
