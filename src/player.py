import os
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QSlider,
    QLabel,
    QStackedWidget,
    QMessageBox,
    QSizePolicy,
)
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget
from PyQt6.QtCore import Qt, QUrl, pyqtSignal
from PyQt6.QtGui import QDesktopServices, QAction, QFont


class MiniPlayer(QWidget):
    # Signal to let the Main Window know a file was deleted so it can refresh the list
    file_deleted = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.current_file = None

        # Main layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(5)

        # --- 1. Display Area (Stack: Video Layer vs Audio Layer) ---
        self.display_stack = QStackedWidget()

        # Layer 0: Video Widget
        self.video_widget = QVideoWidget()
        self.display_stack.addWidget(self.video_widget)

        # Layer 1: Audio Thumbnail / Placeholder
        self.audio_placeholder = QLabel("🎵")
        self.audio_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.audio_placeholder.setStyleSheet(
            "font-size: 80px; background-color: #000; color: #555;"
        )
        self.display_stack.addWidget(self.audio_placeholder)

        self.layout.addWidget(self.display_stack, stretch=1)

        # --- 2. Sliders & Time ---
        time_layout = QHBoxLayout()

        self.lbl_current = QLabel("0:00")
        self.lbl_total = QLabel("0:00")
        self.slider = QSlider(Qt.Orientation.Horizontal)

        time_layout.addWidget(self.lbl_current)
        time_layout.addWidget(self.slider)
        time_layout.addWidget(self.lbl_total)

        self.layout.addLayout(time_layout)

        # --- 3. Controls Area ---
        controls = QHBoxLayout()
        controls.setSpacing(10)

        # Define buttons
        self.btn_open_dir = QPushButton("📂")
        self.btn_open_dir.setToolTip("Open Downloads Folder")

        self.btn_play = QPushButton("▶")
        self.btn_stop = QPushButton("⏹")

        self.btn_delete = QPushButton("🗑️")
        self.btn_delete.setToolTip("Delete current file")
        self.btn_delete.setStyleSheet(
            "QPushButton { color: #ff5555; } QPushButton:hover { background-color: #330000; }"
        )

        # Style standard buttons
        for btn in [self.btn_play, self.btn_stop, self.btn_open_dir, self.btn_delete]:
            btn.setFixedSize(40, 40)
            btn.setStyleSheet(
                btn.styleSheet()
                + "font-size: 18px; border-radius: 5px; background-color: #333;"
            )

        controls.addStretch()
        controls.addWidget(self.btn_open_dir)
        controls.addWidget(self.btn_stop)
        controls.addWidget(self.btn_play)
        controls.addWidget(self.btn_delete)
        controls.addStretch()

        self.layout.addLayout(controls)

        # --- 4. Backend Setup ---
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)
        self.player.setVideoOutput(self.video_widget)

        # Connections
        self.btn_play.clicked.connect(self.toggle_play)
        self.btn_stop.clicked.connect(self.stop_player)
        self.btn_open_dir.clicked.connect(self.open_downloads_folder)
        self.btn_delete.clicked.connect(self.delete_current_file)

        self.player.positionChanged.connect(self.on_position_changed)
        self.player.durationChanged.connect(self.on_duration_changed)
        self.slider.sliderMoved.connect(self.player.setPosition)
        self.slider.sliderPressed.connect(self.player.pause)
        self.slider.sliderReleased.connect(self.player.play)

    def load_media(self, file_path):
        self.stop_player()
        self.current_file = file_path

        # Detect type to switch display mode
        ext = os.path.splitext(file_path)[1].lower()
        if ext in [".mp3", ".m4a", ".wav", ".flac"]:
            # Show Audio Interface
            self.display_stack.setCurrentIndex(1)
            # You could technically load a custom image here if one exists
            self.audio_placeholder.setText("🎵\n" + os.path.basename(file_path))
            self.audio_placeholder.setStyleSheet(
                "font-size: 16px; font-weight: bold; background-color: #222; color: #888;"
            )
        else:
            # Show Video Interface
            self.display_stack.setCurrentIndex(0)

        self.player.setSource(QUrl.fromLocalFile(file_path))
        self.player.play()
        self.btn_play.setText("⏸")
        self.btn_delete.setEnabled(True)

    def toggle_play(self):
        if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.player.pause()
            self.btn_play.setText("▶")
        else:
            self.player.play()
            self.btn_play.setText("⏸")

    def stop_player(self):
        self.player.stop()
        self.btn_play.setText("▶")
        self.slider.setValue(0)
        self.lbl_current.setText("0:00")

    def delete_current_file(self):
        if not self.current_file:
            return

        reply = QMessageBox.question(
            self,
            "Delete File",
            f"Are you sure you want to delete?\n{os.path.basename(self.current_file)}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.stop_player()
            self.player.setSource(QUrl())  # Detach file from player
            try:
                os.remove(self.current_file)
                self.current_file = None
                self.btn_delete.setEnabled(False)
                self.audio_placeholder.setText("Deleted")
                self.file_deleted.emit()  # Tell UI to refresh list
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not delete file:\n{e}")

    def open_downloads_folder(self):
        folder = os.path.join(os.getcwd(), "downloads")
        if not os.path.exists(folder):
            os.makedirs(folder)
        QDesktopServices.openUrl(QUrl.fromLocalFile(folder))

    def on_position_changed(self, position):
        self.slider.setValue(position)
        self.lbl_current.setText(self.format_time(position))

    def on_duration_changed(self, duration):
        self.slider.setMaximum(duration)
        self.lbl_total.setText(self.format_time(duration))

    def format_time(self, ms):
        seconds = (ms // 1000) % 60
        minutes = ms // 60000
        return f"{minutes}:{seconds:02}"


# from PyQt6.QtWidgets import (
#     QWidget,
#     QVBoxLayout,
#     QHBoxLayout,
#     QPushButton,
#     QSlider,
#     QLabel,
# )
# from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
# from PyQt6.QtMultimediaWidgets import QVideoWidget
# from PyQt6.QtCore import Qt, QUrl


# class MiniPlayer(QWidget):
#     def __init__(self):
#         super().__init__()
#         self.layout = QVBoxLayout(self)
#         self.layout.setContentsMargins(0, 0, 0, 0)

#         self.video_widget = QVideoWidget()
#         self.layout.addWidget(self.video_widget)

#         self.player = QMediaPlayer()
#         self.audio_output = QAudioOutput()
#         self.player.setAudioOutput(self.audio_output)
#         self.player.setVideoOutput(self.video_widget)

#         controls = QHBoxLayout()

#         self.btn_play = QPushButton("▶")
#         self.btn_stop = QPushButton("⏹")
#         self.slider = QSlider(Qt.Orientation.Horizontal)

#         for btn in [self.btn_play, self.btn_stop]:
#             btn.setFixedSize(40, 40)
#             btn.setStyleSheet("font-size: 18px; border-radius: 5px;")

#         controls.addWidget(self.btn_play)
#         controls.addWidget(self.btn_stop)
#         controls.addWidget(self.slider)

#         self.layout.addLayout(controls)

#         self.btn_play.clicked.connect(self.toggle_play)
#         self.btn_stop.clicked.connect(self.player.stop)
#         self.player.positionChanged.connect(self.slider.setValue)
#         self.player.durationChanged.connect(self.slider.setMaximum)
#         self.slider.sliderMoved.connect(self.player.setPosition)

#     def load_media(self, file_path):
#         self.player.stop()
#         self.player.setSource(QUrl.fromLocalFile(file_path))
#         self.player.play()
#         self.btn_play.setText("⏸")

#     def toggle_play(self):
#         if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
#             self.player.pause()
#             self.btn_play.setText("▶")
#         else:
#             self.player.play()
#             self.btn_play.setText("⏸")
