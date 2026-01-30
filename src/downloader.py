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

        # Reset to Clean Basics - Disabling cookies as they are currently triggering blocks
        ydl_opts = {
            "outtmpl": os.path.join(self.save_path, "%(title)s [%(id)s].%(ext)s"),
            "restrictfilenames": True,
            "noplaylist": True,
            "quiet": False,
            "no_warnings": False,
            "writethumbnail": False,
            "progress_hooks": [progress_hook],
            "merge_output_format": "mp4",
            "nocheckcertificate": True,
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        }

        # NO COOKIES by default - we proved they cause the 'Only images' error on this account

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
            # Most compatible video format selection
            ydl_opts.update(
                {
                    "format": "bestvideo+bestaudio/best",
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
                if file_size < 100:
                    self.error.emit("Download failed: File is too small or empty.")
                    return
                
                size_mb = file_size / (1024 * 1024)
                self.finished.emit(f"✅ Saved: {os.path.basename(filename)} ({size_mb:.1f} MB)")

        except Exception as e:
            # Show the REAL error with some helpful advice
            error_msg = str(e)
            if "Sign in to confirm your age" in error_msg:
                error_msg = "Error: This video is age-restricted. Your current Chrome cookies are flagged by YouTube, so they cannot be used to bypass this."
            elif "Requested format is not available" in error_msg:
                error_msg = "Error: Format not available. YouTube might be blocking your IP address or the specific video content."
            
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
