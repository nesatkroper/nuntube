import os
from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTabWidget,
    QPushButton,
    QListWidget,
    QLabel,
    QListWidgetItem,
    QMessageBox,
)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import QUrl, Qt
from downloader import DownloaderThread
from player import MiniPlayer

DARK_STYLESHEET = """
QMainWindow, QWidget { background-color: #1e1e1e; color: #ffffff; }
QTabWidget::pane { border: 1px solid #333; }
QTabBar::tab { background: #2d2d2d; padding: 10px 20px; color: #aaa; }
QTabBar::tab:selected { background: #3d3d3d; color: #fff; border-bottom: 2px solid #007acc; }
QPushButton { background-color: #333; border: none; padding: 8px; border-radius: 4px; color: white; }
QPushButton:hover { background-color: #444; }
QPushButton:disabled { background-color: #555; color: #888; }
QListWidget { background-color: #252525; border: none; font-size: 14px; }
QListWidget::item { padding: 10px; border-bottom: 1px solid #333; }
QListWidget::item:selected { background-color: #3d3d3d; }
QSlider::handle:horizontal { background: #007acc; width: 10px; margin: -4px 0; border-radius: 5px; }
"""


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Minimal YouTube Downloader")
        self.showMaximized()
        self.setStyleSheet(DARK_STYLESHEET)

        self.download_path = os.path.join(os.getcwd(), "downloads")
        if not os.path.exists(self.download_path):
            os.makedirs(self.download_path)

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        self.setup_browser_tab()
        self.setup_downloads_tab()

    def setup_browser_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.browser = QWebEngineView()
        self.browser.setUrl(QUrl("https://www.youtube.com"))
        self.browser.urlChanged.connect(self.on_url_change)

        self.overlay = QWidget()
        self.overlay.setFixedHeight(80)
        self.overlay.setStyleSheet(
            "background-color: #252525; border-top: 2px solid #007acc;"
        )
        self.overlay.hide()

        overlay_layout = QHBoxLayout(self.overlay)

        self.status_label = QLabel("Ready")
        self.status_label.setFixedWidth(200)

        self.btn_mp3 = QPushButton("🎵 Download MP3")
        self.btn_mp3.clicked.connect(lambda: self.start_download("mp3"))

        self.btn_mp4 = QPushButton("🎬 Download MP4")
        self.btn_mp4.clicked.connect(lambda: self.start_download("mp4"))

        for btn in [self.btn_mp3, self.btn_mp4]:
            btn.setFixedWidth(160)
            btn.setStyleSheet(
                "font-weight: bold; font-size: 14px; background-color: #007acc;"
            )

        overlay_layout.addStretch()
        overlay_layout.addWidget(self.status_label)
        overlay_layout.addSpacing(20)
        overlay_layout.addWidget(self.btn_mp3)
        overlay_layout.addWidget(self.btn_mp4)
        overlay_layout.addStretch()

        layout.addWidget(self.browser)
        layout.addWidget(self.overlay)
        self.tabs.addTab(tab, "🌏 Browser")

    def setup_downloads_tab(self):
        tab = QWidget()
        layout = QHBoxLayout(tab)

        self.file_list = QListWidget()
        self.file_list.setMaximumWidth(400)
        self.file_list.itemClicked.connect(self.play_file)

        self.player_area = MiniPlayer()
        self.player_area.file_deleted.connect(self.refresh_file_list)

        layout.addWidget(self.file_list)
        layout.addWidget(self.player_area)

        self.tabs.addTab(tab, "📂 Downloads")
        self.tabs.currentChanged.connect(self.refresh_file_list)

    def on_url_change(self, url):
        url_str = url.toString()
        if "watch?v=" in url_str or "shorts/" in url_str:
            self.overlay.show()
        else:
            self.overlay.hide()

    def start_download(self, mode):
        self.btn_mp3.setEnabled(False)
        self.btn_mp4.setEnabled(False)
        self.status_label.setText("Initializing...")

        url = self.browser.url().toString()
        self.thread = DownloaderThread(url, mode)

        self.thread.progress.connect(self.status_label.setText)
        self.thread.finished.connect(self.on_download_finished)
        self.thread.error.connect(self.on_download_error)

        self.thread.start()

    def on_download_finished(self, msg):
        self.status_label.setText("✅ Done!")
        self.btn_mp3.setEnabled(True)
        self.btn_mp4.setEnabled(True)
        self.refresh_file_list()

    def on_download_error(self, err_msg):
        self.status_label.setText("❌ Error")
        QMessageBox.critical(self, "Download Error", err_msg)
        self.btn_mp3.setEnabled(True)
        self.btn_mp4.setEnabled(True)

    def refresh_file_list(self):
        if self.tabs.currentIndex() != 1:
            return

        self.file_list.clear()
        if not os.path.exists(self.download_path):
            return

        files = sorted(
            os.listdir(self.download_path),
            key=lambda x: os.path.getctime(os.path.join(self.download_path, x)),
            reverse=True,
        )

        for f in files:
            if f.endswith((".mp3", ".mp4", ".m4a", ".webm")):
                icon = "🎵" if f.endswith(".mp3") else "🎬"
                item = QListWidgetItem(f"{icon}  {f}")
                item.setData(
                    Qt.ItemDataRole.UserRole, os.path.join(self.download_path, f)
                )
                self.file_list.addItem(item)

    def play_file(self, item):
        path = item.data(Qt.ItemDataRole.UserRole)
        self.player_area.load_media(path)
