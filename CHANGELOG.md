# Changelog

## [Latest Update] - 2026-01-30

### ✨ New Features

#### 1. **Persistent Browser Sessions** 🔐

- The browser now remembers your login sessions and cookies
- You can sign in to YouTube (or any site) and stay logged in between app restarts
- Browser data is stored in the `browser_profile/` directory
- Uses QWebEngineProfile with persistent storage for cookies and session data

#### 2. **MP4 Video Downloads** 🎬

- Added a new "Download MP4" button alongside the existing "Download MP3" button
- Both buttons appear when you're on a YouTube video page
- Download high-quality MP4 videos with H.264 codec for maximum compatibility
- Modern pill-style buttons with icons for better UX

### 🔧 Technical Changes

**Files Modified:**

- `src/ui.py`:
  - Added `QWebEngineProfile` import for persistent sessions
  - Created `browser_profile/` directory for storing browser data
  - Added persistent profile configuration with `ForcePersistentCookies` policy
  - Added MP4 download button with matching styling
  - Updated button enable/disable logic to handle both MP3 and MP4 buttons

- `.gitignore`:
  - Added `browser_profile/` to keep user sessions private

### 📝 Usage

**Persistent Sessions:**

- Simply log in to YouTube (or any website) as you normally would
- Your session will be saved automatically
- Next time you open the app, you'll still be logged in

**Downloading:**

- Navigate to any YouTube video
- Click "🎵 Download MP3" for audio-only (192kbps MP3)
- Click "🎬 Download MP4" for video (H.264 codec)
- Files are saved to the `downloads/` folder

### 🐛 Bug Fixes

- Fixed missing `libxcb-cursor0` dependency issue on Ubuntu 24.04
- Both download buttons are properly disabled during active downloads to prevent conflicts

### 🎨 Design

- Maintained the existing dark theme and modern UI
- Both download buttons use consistent pill-style design
- Added emojis to buttons for better visual clarity
