import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
import yt_dlp
import pygame
from mutagen.id3 import ID3, APIC
import webbrowser
import sys

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")


def get_asset_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    base_path = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


class DownloadCancelled(Exception):
    pass


class YouTubeDownloaderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("NunTube - YouTube Channel MP3 Downloader")
        self.root.geometry("1200x800")
        self.set_app_icon()
        self.root.resizable(True, True)

        # Variables
        self.channel_url = tk.StringVar()
        self.save_path = tk.StringVar(value=os.path.expanduser("~/Downloads"))
        self.progress = tk.DoubleVar(value=0)

        self.current_video = 0
        self.total_videos = 0
        self.stop_download = False

        self.current_save_dir = None
        self.displayed_dir = None
        self.playing_file = None

        # UI References
        self.mp3_scroll_frame = None
        self.log_text = None
        self.left_frame = None
        self.right_frame = None
        self.download_button = None

        # Initialize pygame mixer
        pygame.mixer.init()

        # UI Elements
        self.create_ui()

    def set_app_icon(self):
        """Finds the icon and applies it to the window."""
        try:
            # Make sure this matches your folder structure (e.g., assets/download.png)
            icon_path = get_asset_path("assets/download.png")
            if os.path.exists(icon_path):
                img = tk.PhotoImage(file=icon_path)
                self.root.iconphoto(True, img)
            else:
                print(f"Icon not found at: {icon_path}")
        except Exception as e:
            print(f"Failed to load icon: {e}")

    def create_ui(self):
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_rowconfigure(1, weight=0)
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=1)

        # --- Frames ---
        self.left_frame = ctk.CTkFrame(self.root)
        self.left_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        self.right_frame = ctk.CTkFrame(self.root)
        self.right_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

        # Footer
        footer_frame = ctk.CTkFrame(self.root)
        footer_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=10, pady=10)
        credit_button = ctk.CTkButton(
            footer_frame,
            text="Developed by Suon Phanun",
            command=self.open_credit_links,
        )
        credit_button.pack(fill=tk.X)

        # --- Left Side (Download) ---
        url_label = ctk.CTkLabel(self.left_frame, text="YouTube Channel URL:")
        url_label.pack(pady=10, fill=tk.X)

        url_entry = ctk.CTkEntry(
            self.left_frame, textvariable=self.channel_url, width=500
        )
        url_entry.pack(fill=tk.X)

        path_label = ctk.CTkLabel(self.left_frame, text="Save Path:")
        path_label.pack(pady=10, fill=tk.X)

        path_frame = ctk.CTkFrame(self.left_frame)
        path_frame.pack(fill=tk.X)

        path_entry = ctk.CTkEntry(path_frame, textvariable=self.save_path, width=400)
        path_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        browse_button = ctk.CTkButton(
            path_frame, text="Browse", command=self.browse_path
        )
        browse_button.pack(side=tk.LEFT, padx=5)

        self.progress_bar = ctk.CTkProgressBar(
            self.left_frame, variable=self.progress, width=500
        )
        self.progress_bar.pack(pady=20, fill=tk.X)

        log_label = ctk.CTkLabel(self.left_frame, text="Process Log:")
        log_label.pack(pady=5, fill=tk.X)

        self.log_text = ctk.CTkTextbox(self.left_frame, height=200, width=500)
        self.log_text.pack(pady=10, fill=tk.BOTH, expand=True)
        self.log_text.configure(state="disabled")

        self.download_button = ctk.CTkButton(
            self.left_frame, text="Start download MP3", command=self.start_download
        )
        self.download_button.pack(pady=20, fill=tk.X)

        # --- Right Side (MP3 List) ---
        mp3_label = ctk.CTkLabel(self.right_frame, text="Downloaded MP3s")
        mp3_label.pack(pady=10, fill=tk.X)

        reload_button = ctk.CTkButton(
            self.right_frame, text="Reload List", command=self.reload_mp3_list
        )
        reload_button.pack(pady=5, fill=tk.X)

        browse_mp3_button = ctk.CTkButton(
            self.right_frame, text="Browse MP3 Folder", command=self.browse_mp3_folder
        )
        browse_mp3_button.pack(pady=5, fill=tk.X)

        self.thumbnail_button = ctk.CTkButton(
            self.right_frame,
            text="Set Thumbnail for All MP3s",
            command=self.set_thumbnails,
        )
        self.thumbnail_button.pack(pady=10, fill=tk.X)

        # [FIX] Create the scroll frame ONCE here, instead of recreating it every time
        self.mp3_scroll_frame = ctk.CTkScrollableFrame(
            self.right_frame, width=500, label_text="MP3 List"
        )
        self.mp3_scroll_frame.pack(pady=10, fill=tk.BOTH, expand=True)

        # Populate initially
        self.show_mp3_list(None)

    def open_credit_links(self):
        webbrowser.open("https://t.me/devphanun")

    def log_message(self, message):
        self.log_text.configure(state="normal")
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.configure(state="disabled")
        self.log_text.see(tk.END)

    def browse_path(self):
        path = filedialog.askdirectory(initialdir=self.save_path.get())
        if path:
            self.save_path.set(path)

    def browse_mp3_folder(self):
        path = filedialog.askdirectory(initialdir=self.save_path.get())
        if path:
            self.displayed_dir = path
            self.show_mp3_list(path)

    def reload_mp3_list(self):
        # [FIX] Better reload logic using the specific variable tracking the displayed folder
        target_dir = self.displayed_dir or self.current_save_dir
        if target_dir and os.path.isdir(target_dir):
            self.show_mp3_list(target_dir)
        else:
            messagebox.showinfo(
                "Info", "No MP3 folder selected yet.\nUse 'Browse MP3 Folder' first."
            )

    def show_mp3_list(self, save_dir):
        # [FIX] Instead of destroying self.mp3_scroll_frame, clear its children
        for widget in self.mp3_scroll_frame.winfo_children():
            widget.destroy()

        text = None
        if not save_dir or not os.path.exists(save_dir):
            text = "No MP3s loaded yet."
        else:
            # Recursively find MP3s
            mp3_files = []
            for root, dirs, files in os.walk(save_dir):
                for f in files:
                    if f.lower().endswith(".mp3"):
                        mp3_files.append(os.path.join(root, f))

            mp3_files = sorted(mp3_files)

            if not mp3_files:
                text = "No MP3 files found in this folder."
            else:
                for full_path in mp3_files:
                    rel_path = os.path.relpath(full_path, save_dir)

                    # Create a row for each file
                    frame = ctk.CTkFrame(self.mp3_scroll_frame)
                    frame.pack(fill=tk.X, pady=5)

                    label = ctk.CTkLabel(frame, text=rel_path, anchor="w")
                    label.pack(side=tk.LEFT, padx=10, expand=True, fill=tk.X)

                    play_btn = ctk.CTkButton(
                        frame,
                        text="▶",
                        width=40,
                        command=lambda f=full_path: self.play_mp3(f),
                    )
                    play_btn.pack(side=tk.LEFT, padx=5)

                    stop_btn = ctk.CTkButton(
                        frame,
                        text="■",
                        width=40,
                        fg_color="yellow",
                        text_color="black",
                        command=self.stop_mp3,
                    )
                    stop_btn.pack(side=tk.LEFT, padx=5)

                    delete_btn = ctk.CTkButton(
                        frame,
                        text="🗑",
                        width=40,
                        fg_color="red",
                        command=lambda f=full_path: self.delete_mp3(f),
                    )
                    delete_btn.pack(side=tk.LEFT, padx=5)

        if text:
            empty_label = ctk.CTkLabel(self.mp3_scroll_frame, text=text)
            empty_label.pack(pady=20)

    def play_mp3(self, file):
        if self.playing_file:
            self.stop_mp3()
        try:
            pygame.mixer.music.load(file)
            pygame.mixer.music.play()
            self.playing_file = file
        except Exception as e:
            messagebox.showerror("Playback Error", f"Could not play file:\n{e}")

    def stop_mp3(self):
        if self.playing_file:
            pygame.mixer.music.stop()
            self.playing_file = None

    def delete_mp3(self, file):
        try:
            self.stop_mp3()  # Stop before deleting
            os.remove(file)
            # Reload current list
            self.reload_mp3_list()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete {file}: {str(e)}")

    def set_thumbnails(self):
        dir_to_use = self.displayed_dir or self.current_save_dir or self.save_path.get()

        if not os.path.isdir(dir_to_use):
            messagebox.showerror(
                "Error", "No valid directory set. Please Browse MP3 Folder first."
            )
            return

        image_path = filedialog.askopenfilename(
            title="Select Thumbnail Image", filetypes=[("Image files", "*.jpg *.png")]
        )
        if not image_path:
            return

        mp3_files = []
        for root, dirs, files in os.walk(dir_to_use):
            for f in files:
                if f.endswith(".mp3"):
                    mp3_files.append(os.path.join(root, f))

        total = len(mp3_files)
        if total == 0:
            messagebox.showinfo("Info", "No MP3 files found to update.")
            return

        self.progress.set(0)
        self.log_message("Setting thumbnails...")

        # Run in thread to prevent freezing
        threading.Thread(
            target=self._process_thumbnails, args=(mp3_files, image_path), daemon=True
        ).start()

    def _process_thumbnails(self, mp3_files, image_path):
        total = len(mp3_files)
        with open(image_path, "rb") as img:
            data = img.read()

        mime = "image/jpeg" if image_path.lower().endswith(".jpg") else "image/png"

        for i, mp3_file in enumerate(mp3_files):
            try:
                audio = ID3(mp3_file)
                audio.add(APIC(encoding=3, mime=mime, type=3, desc="Cover", data=data))
                audio.save()
            except Exception as e:
                print(f"Error on {mp3_file}: {e}")

            # Update progress safely
            progress_val = (i + 1) / total
            self.progress.set(progress_val)

        self.log_message("Thumbnails set!")
        self.root.after(
            0, lambda: messagebox.showinfo("Success", "Thumbnails updated!")
        )

    # ... Download logic remains mostly same, just ensuring variables are used correctly ...
    def start_download(self):
        url = self.channel_url.get().strip()
        if not url:
            messagebox.showerror("Error", "Please enter a YouTube channel URL.")
            return

        self.progress.set(0)
        self.log_message("Initializing...")
        self.stop_download = False

        self.download_button.configure(
            text="Stop Download", command=self.stop_download_func, fg_color="red"
        )

        threading.Thread(target=self.download_channel, args=(url,), daemon=True).start()

    def stop_download_func(self):
        self.stop_download = True
        self.log_message("Stopping download...")

    def download_channel(self, url):
        try:
            ydl_opts_info = {"quiet": True, "extract_flat": True}
            with yt_dlp.YoutubeDL(ydl_opts_info) as ydl:
                info = ydl.extract_info(url, download=False)
                channel_name = info.get("uploader", "Unknown_Channel").replace(" ", "_")

            save_dir = os.path.join(self.save_path.get(), channel_name)
            os.makedirs(save_dir, exist_ok=True)
            self.current_save_dir = save_dir

            if "/channel/" in url or "/user/" in url or "/c/" in url or "/@" in url:
                videos_url = url.rstrip("/") + "/videos"
            else:
                videos_url = url

            self.log_message("Extracting playlist...")
            with yt_dlp.YoutubeDL(ydl_opts_info) as ydl:
                playlist_info = ydl.extract_info(videos_url, download=False)
                entries = playlist_info["entries"]
                self.total_videos = len(entries)

            ydl_opts = {
                "format": "bestaudio/best",
                "postprocessors": [
                    {
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "mp3",
                        "preferredquality": "192",
                    }
                ],
                "outtmpl": os.path.join(save_dir, "%(title)s.%(ext)s"),
                "quiet": False,
                "progress_hooks": [self.progress_hook],
                "ignoreerrors": True,
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                for i, entry in enumerate(entries):
                    if self.stop_download:
                        break
                    self.current_video = i + 1
                    self.log_message(
                        f"Downloading {self.current_video}/{self.total_videos}: {entry.get('title', 'Unknown')}"
                    )
                    ydl.download([entry["url"]])

            if not self.stop_download:
                self.log_message("Download Complete!")
                self.root.after(
                    0, lambda: messagebox.showinfo("Success", "Download Complete")
                )

        except Exception as e:
            self.log_message(f"Error: {str(e)}")
        finally:
            if self.current_save_dir:
                self.displayed_dir = self.current_save_dir
                self.root.after(0, lambda: self.show_mp3_list(self.current_save_dir))

            self.root.after(0, self._reset_download_ui)

    def _reset_download_ui(self):
        self.progress.set(0)
        self.download_button.configure(
            text="Download Channel as MP3",
            command=self.start_download,
            fg_color="#1f538d",
        )
        self.stop_download = False

    def progress_hook(self, d):
        if self.stop_download:
            raise DownloadCancelled("Stopped")
        if d["status"] == "downloading":
            p = d.get("_percent_str", "0%").replace("%", "")
            try:
                self.progress.set(float(p) / 100)
            except:
                pass


if __name__ == "__main__":
    root = ctk.CTk(className="nuntube")
    app = YouTubeDownloaderApp(root)
    root.mainloop()
