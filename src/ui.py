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
    QHBoxLayout,
    QSpacerItem,
    QSizePolicy,
)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineProfile
from PyQt6.QtCore import QUrl, Qt
from downloader import DownloaderThread
from player import MiniPlayer

DARK_STYLESHEET = """
QMainWindow, QWidget { background-color: #1e1e1e; color: #ffffff; }
QTabWidget::pane { border: 1px solid #333; }
QTabBar::tab { background: #2d2d2d; padding: 6px 16px; color: #aaa; font-size: 12px; font-weight: bold; }
QTabBar::tab:selected { background: #3d3d3d; color: #fff; border-bottom: 2px solid #007acc; }
QPushButton { background-color: #333; border: none; padding: 6px; border-radius: 4px; color: white; }
QPushButton:hover { background-color: #444; }
QPushButton:disabled { background-color: #555; color: #888; }
QListWidget { background-color: #252525; border: none; font-size: 13px; outline: none; }
QListWidget::item { padding: 8px; border-bottom: 1px solid #333; }
QListWidget::item:selected { background-color: #007acc; color: white; border-bottom: 1px solid #007acc; }
QSlider::handle:horizontal { background: #007acc; width: 10px; margin: -4px 0; border-radius: 5px; }
"""


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Kouprey Tube")
        self.showMaximized()
        self.setStyleSheet(DARK_STYLESHEET)

        self.download_path = os.path.join(os.getcwd(), "downloads")
        if not os.path.exists(self.download_path):
            os.makedirs(self.download_path)

        # Create persistent profile directory for browser cookies/sessions
        self.profile_path = os.path.join(os.getcwd(), "browser_profile")
        if not os.path.exists(self.profile_path):
            os.makedirs(self.profile_path)

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        
        # Setup Header (Corner Widget)
        self.setup_header()

        self.setup_browser_tab()
        self.setup_downloads_tab()


    def setup_header(self):
        self.header_widget = QWidget()
        header_layout = QHBoxLayout(self.header_widget)
        header_layout.setContentsMargins(0, 0, 10, 0) 
        header_layout.setSpacing(10)

        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #007acc; font-size: 11px; font-weight: bold;")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        self.btn_mp4 = QPushButton("🎬 Download")
        self.btn_mp4.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_mp4.clicked.connect(lambda: self.start_download("mp4"))
        self.btn_mp4.setFixedWidth(110)
        self.btn_mp4.setFixedHeight(26) # Height matches tab bar area better
        self.btn_mp4.setEnabled(False)
        
        self.btn_mp4.setStyleSheet("""
            QPushButton {
                background-color: #007acc;
                border: none;
                border-radius: 13px;
                color: white;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #008ae6;
            }
            QPushButton:disabled {
                background-color: #333;
                color: #555;
            }
        """)

        header_layout.addWidget(self.status_label)
        header_layout.addWidget(self.btn_mp4)
        
        self.tabs.setCornerWidget(self.header_widget, Qt.Corner.TopRightCorner)

    def setup_browser_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Create persistent profile for cookies/login sessions
        self.profile = QWebEngineProfile("KoupreyProfile", self)
        self.profile.setPersistentStoragePath(self.profile_path)
        self.profile.setPersistentCookiesPolicy(
            QWebEngineProfile.PersistentCookiesPolicy.ForcePersistentCookies
        )

        # Create browser with persistent profile
        from PyQt6.QtWebEngineCore import QWebEnginePage
        page = QWebEnginePage(self.profile, self)
        self.browser = QWebEngineView()
        self.browser.setPage(page)
        self.browser.setUrl(QUrl("https://www.youtube.com"))
        self.browser.urlChanged.connect(self.on_url_change)
        
        layout.addWidget(self.browser)
        self.tabs.addTab(tab, "🌏 Browser")


    def setup_downloads_tab(self):
        tab = QWidget()
        layout = QHBoxLayout(tab)

        self.file_list = QListWidget()
        self.file_list.itemClicked.connect(self.play_file)

        self.player_area = MiniPlayer()
        self.player_area.file_deleted.connect(self.refresh_file_list)

        # 30% Left (List), 70% Right (Player) - Making player bigger
        layout.addWidget(self.file_list, 3)
        layout.addWidget(self.player_area, 7)

        self.tabs.addTab(tab, "📂 Downloads")
        self.tabs.currentChanged.connect(self.refresh_file_list)

    def on_url_change(self, url):
        url_str = url.toString()
        is_video = "watch?v=" in url_str or "shorts/" in url_str
        self.btn_mp4.setEnabled(is_video)
        if not is_video:
            self.status_label.setText("")

    def start_download(self, mode):
        self.btn_mp4.setEnabled(False)
        self.status_label.setText("Initializing...")

        url = self.browser.url().toString()
        
        # Pass profile path (yt-dlp will handle cookie extraction internally)
        self.thread = DownloaderThread(url, mode, self.profile_path)

        self.thread.progress.connect(self.status_label.setText)
        self.thread.finished.connect(self.on_download_finished)
        self.thread.error.connect(self.on_download_error)

        self.thread.start()

    def on_download_finished(self, msg):
        self.status_label.setText("✅ Done!")
        self.btn_mp4.setEnabled(True)
        self.refresh_file_list()

    def on_download_error(self, err_msg):
        self.status_label.setText("❌ Error")
        QMessageBox.critical(self, "Download Error", err_msg)
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
