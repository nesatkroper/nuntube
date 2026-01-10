import os
import yt_dlp
from PyQt6.QtCore import QThread, pyqtSignal


class DownloaderThread(QThread):
    progress = pyqtSignal(str)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, url, mode):
        super().__init__()
        self.url = url
        self.mode = mode
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

        # Base options
        ydl_opts = {
            "outtmpl": os.path.join(self.save_path, "%(title)s [%(id)s].%(ext)s"),
            "restrictfilenames": True,
            "noplaylist": True,
            "quiet": True,
            "progress_hooks": [progress_hook],
            "merge_output_format": "mp4",
        }

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
            # Video settings: Forces H.264 (avc1) for maximum compatibility with PyQt6
            # This avoids the AV1 decoding errors you encountered.
            ydl_opts.update(
                {
                    "format": "bestvideo[vcodec^=avc1]+bestaudio[ext=m4a]/best[vcodec^=avc1]/best",
                }
            )

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # extract_info with download=True handles the full process
                info = ydl.extract_info(self.url, download=True)
                filename = ydl.prepare_filename(info)

                # If we converted to MP3, the extension in 'filename' might still be the original
                if self.mode == "mp3":
                    filename = os.path.splitext(filename)[0] + ".mp3"

            self.finished.emit(f"Saved: {os.path.basename(filename)}")

        except Exception as e:
            # Send the error message back to the UI
            self.error.emit(str(e))


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
