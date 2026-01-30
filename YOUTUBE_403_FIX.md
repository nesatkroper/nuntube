# YouTube Download 403 Error - Fix Guide

## Problem

YouTube blocks automated downloads with **HTTP 403 Forbidden** errors to prevent bots.

## Solution Implemented

### 1. **Browser Cookie Integration** 🍪

- The app now uses cookies from your browser session
- When you're logged into YouTube in the app, downloads use your authenticated session
- This makes YouTube think the download is coming from a real browser

### 2. **Anti-Bot Measures** 🤖

- **User-Agent Spoofing**: Pretends to be Chrome browser
- **Referer Header**: Tells YouTube the request came from youtube.com
- **Android Player Client**: Uses YouTube's mobile API which is more reliable
- **Player Skip**: Bypasses some YouTube restrictions

### 3. **Better Format Selection** 📹

- Limited to 1080p max (more reliable than 4K)
- Prefers H.264 codec for best compatibility
- Falls back to alternative formats if primary fails

## How It Works

```
Browser (You logged in) → Cookies saved → yt-dlp uses cookies → YouTube allows download
```

## Troubleshooting

### If downloads still fail:

1. **Make sure you're logged into YouTube in the browser tab**
   - Click the Browser tab
   - Log into your YouTube account
   - Wait a few seconds for cookies to save
   - Try downloading again

2. **Try a different video**
   - Some videos have additional restrictions (age-restricted, region-locked, etc.)
   - Music videos often have stricter protection

3. **Clear browser profile and re-login**

   ```bash
   rm -rf browser_profile/
   # Then restart app and log in again
   ```

4. **Check yt-dlp version**
   ```bash
   pip install --upgrade yt-dlp
   ```

## Technical Details

The downloader now:

- Uses `cookiesfrombrowser` to extract Chrome cookies
- Sets proper user-agent and referer headers
- Uses Android and Web player clients as fallback
- Limits video quality to 1080p for better success rate

## Alternative: Use OAuth (Future Enhancement)

For even better reliability, we could add:

- YouTube OAuth login
- Direct API access
- Premium account integration
