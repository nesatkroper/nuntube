import os
import yt_dlp
from PyQt6.QtCore import QThread, pyqtSignal


class DownloaderThread(QThread):
    progress = pyqtSignal(str)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, url, mode, profile_path=None):
        super().__init__()
        self.url = url
        self.mode = mode
        self.profile_path = profile_path
        self.save_path = os.path.join(os.getcwd(), "downloads")
        if not os.path.exists(self.save_path):
            os.makedirs(self.save_path)

    def run(self):
        def progress_hook(d):
            if d["status"] == "downloading":
                # Extract percentage and speed for better feedback
                p = d.get("_percent_str", "0%").replace("%", "").strip()
                self.progress.emit(f"Downloading: {p}%")
            elif d["status"] == "finished":
                self.progress.emit("Finalizing file...")

        # Options optimized for stability
        ydl_opts = {
            "outtmpl": os.path.join(self.save_path, "%(title)s [%(id)s].%(ext)s"),
            "restrictfilenames": True,
            "noplaylist": True,
            "quiet": False,  # Turn on some logging for debugging
            "no_warnings": False,
            "writethumbnail": False, # Disable thumbnails to avoid confusion
            "progress_hooks": [progress_hook],
            "merge_output_format": "mp4",
            "nocheckcertificate": True,
        }

        # Use the app's own browser profile for cookies
        if self.profile_path and os.path.exists(self.profile_path):
            try:
                # On Linux, Chrome/QtWebEngine cookies are in the profile root
                # yt-dlp can sometimes read from a directory if passed as chrome:path
                ydl_opts["cookiesfrombrowser"] = (f"chrome:{self.profile_path}",)
            except Exception as e:
                print(f"Cookie extraction failed: {e}")
        else:
            # Fallback to system chrome
            try:
                ydl_opts["cookiesfrombrowser"] = ("chrome",)
            except:
                pass

        if self.mode == "mp3":
            # Audio-only settings
            ydl_opts.update(
                {
                    "format": "bestaudio/best",
                    "postprocessors": [
                        {
                            "key": "FFmpegExtractAudio",
                            "preferredcodec": "mp3",
                            "preferredquality": "192",
                        }
                    ],
                }
            )
        else:
            # Video settings - get best but avoid problematic formats
            ydl_opts.update(
                {
                    "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
                }
            )

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(self.url, download=True)
                filename = ydl.prepare_filename(info)

                if self.mode == "mp3":
                    # After FFmpegExtractAudio, the extension is changed
                    filename = os.path.splitext(filename)[0] + ".mp3"

                # Wait a tiny bit for file system
                import time
                time.sleep(0.5)

                if not os.path.exists(filename):
                    self.error.emit(f"Download Error: File not found at {os.path.basename(filename)}")
                    return
                
                file_size = os.path.getsize(filename)
                if file_size < 100:  # If less than 100 bytes, it's definitely not a video/audio
                    self.error.emit("Download failed: File is too small or empty. YouTube might be blocking this request.")
                    return
                
                size_mb = file_size / (1024 * 1024)
                self.finished.emit(f"✅ Saved: {os.path.basename(filename)} ({size_mb:.1f} MB)")

        except Exception as e:
            # Send the error message back to the UI
            error_msg = str(e)
            # Make error messages more user-friendly
            if "Requested format is not available" in error_msg:
                error_msg = "Format not available. Try a different video or install Node.js (see YOUTUBE_RESTRICTIONS.md)"
            elif "Only images are available" in error_msg:
                error_msg = "This content (Short/Post) cannot be downloaded as video"
            
            self.error.emit(error_msg)




# import os
# import yt_dlp
# from PyQt6.QtCore import QThread, pyqtSignal


# class DownloaderThread(QThread):
#     progress = pyqtSignal(str)
#     finished = pyqtSignal(str)
#     error = pyqtSignal(str)

#     def __init__(self, url, mode):
#         super().__init__()
#         self.url = url
#         self.mode = mode
#         self.save_path = os.path.join(os.getcwd(), "downloads")
#         if not os.path.exists(self.save_path):
#             os.makedirs(self.save_path)

#     def run(self):
#         def progress_hook(d):
#             if d["status"] == "downloading":
#                 p = d.get("_percent_str", "0%").replace("%", "")
#                 self.progress.emit(f"Downloading: {p}%")
#             elif d["status"] == "finished":
#                 self.progress.emit("Processing...")

#         ydl_opts = {
#             "outtmpl": os.path.join(self.save_path, "%(title)s [%(id)s].%(ext)s"),
#             "restrictfilenames": True,
#             "noplaylist": True,
#             "quiet": True,
#             "progress_hooks": [progress_hook],
#             "format": "bv*[vcodec^=avc1]+ba/best[vcodec^=avc1]/best",
#             "merge_output_format": "mp4",
#         }

#         if self.mode == "mp3":
#             ydl_opts.update(
#                 {
#                     "format": "bestaudio/best",
#                     "postprocessors": [
#                         {
#                             "key": "FFmpegExtractAudio",
#                             "preferredcodec": "mp3",
#                             "preferredquality": "192",
#                         }
#                     ],
#                 }
#             )
#         else:
#             ydl_opts.update(
#                 {
#                     "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
#                 }
#             )

#         try:
#             with yt_dlp.YoutubeDL(ydl_opts) as ydl:
#                 info = ydl.extract_info(self.url, download=True)
#                 filename = ydl.prepare_filename(info)

#                 if self.mode == "mp3":
#                     filename = os.path.splitext(filename)[0] + ".mp3"

#             self.finished.emit(f"Saved: {os.path.basename(filename)}")
#         except Exception as e:
#             self.error.emit(str(e))
