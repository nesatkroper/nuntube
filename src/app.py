import sys
import os

# Disable GPU acceleration to fix SIGSEGV on some Linux systems
os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--disable-gpu"
os.environ["QT_X11_NO_MITSHM"] = "1"
os.environ["QTWEBENGINE_DISABLE_SANDBOX"] = "1"

from PyQt6.QtWidgets import QApplication
from ui import MainWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = MainWindow()

    sys.exit(app.exec())
