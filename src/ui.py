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
        self.setWindowTitle("Kouoprey - YouTube Downloader")
        self.showMaximized()
        self.setStyleSheet(DARK_STYLESHEET)

        self.download_path = os.path.join(os.getcwd(), "downloads")
        if not os.path.exists(self.download_path):
            os.makedirs(self.download_path)

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        self.setup_browser_tab()
        self.setup_downloads_tab()

        # Footer
        footer_frame = ctk.CTkFrame(self.root)
        footer_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=10, pady=10)
        credit_button = ctk.CTkButton(
            footer_frame,
            text="Developed by Suon Phanun",
            command=self.open_credit_links,
        )
        credit_button.pack(fill=tk.X)

    def setup_browser_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.browser = QWebEngineView()
        self.browser.setUrl(QUrl("https://www.youtube.com"))
        self.browser.urlChanged.connect(self.on_url_change)

        self.overlay = QWidget()
        self.overlay.setFixedHeight(60)  # Reduced height
        self.overlay.setStyleSheet(
            "background-color: #252525;"
        )
        self.overlay.hide()

        overlay_layout = QHBoxLayout(self.overlay)

        self.status_label = QLabel("Ready")
        self.status_label.setFixedWidth(600)  # Set fixed width
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.status_label.setStyleSheet("color: #aaa; font-size: 13px; font-weight: bold;")

        self.btn_mp3 = QPushButton("Download Audio (MP3)")
        self.btn_mp3.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_mp3.clicked.connect(lambda: self.start_download("mp3"))
        self.btn_mp3.setFixedWidth(180)  # Smaller width
        self.btn_mp3.setFixedHeight(36)  # Smaller height
        
        # Modern Pill Button Styling
        self.btn_mp3.setStyleSheet("""
            QPushButton {
                background-color: #007acc;
                border: none;
                border-radius: 18px;
                color: white;
                font-size: 13px;
                font-weight: bold;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #0062a3;
                margin-top: 1px;
            }
            QPushButton:disabled {
                background-color: #333;
                color: #777;
            }
        """)

        # Container Layout
        container = QWidget()
        container_layout = QHBoxLayout(container)
        container_layout.setContentsMargins(20, 5, 20, 5)  # Reduced vertical margins
        
        # Add widgets side by side
        container_layout.addWidget(self.status_label, alignment=Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        container_layout.addStretch() # Spacer between them
        container_layout.addWidget(self.btn_mp3, alignment=Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        overlay_layout.addWidget(container)
        
        layout.addWidget(self.browser)
        layout.addWidget(self.overlay)
        self.tabs.addTab(tab, "🌏 Browser")

    def setup_downloads_tab(self):
        tab = QWidget()
        layout = QHBoxLayout(tab)

        self.file_list = QListWidget()
        self.file_list.itemClicked.connect(self.play_file)

        self.player_area = MiniPlayer()
        self.player_area.file_deleted.connect(self.refresh_file_list)

        # 60% Left (List), 40% Right (Player)
        layout.addWidget(self.file_list, 6)
        layout.addWidget(self.player_area, 4)

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
        self.refresh_file_list()

    def on_download_error(self, err_msg):
        self.status_label.setText("❌ Error")
        QMessageBox.critical(self, "Download Error", err_msg)
        self.btn_mp3.setEnabled(True)

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
