import sys
import os
from PyQt5.QtWidgets import QApplication, QLabel, QFileDialog, QMenu, QDialog, QVBoxLayout, QLineEdit, QPushButton, QLabel as QLabelWidget, QMessageBox
from PyQt5.QtGui import QPixmap, QMovie
from PyQt5.QtCore import Qt, QSize, QCoreApplication

CONFIG_FILE = "config.txt"

DEFAULT_MAX_WIDTH = 1920
DEFAULT_MAX_HEIGHT = 1080

class OptionsDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("설정")
        self.setFixedSize(300, 180)

        self.parent = parent
        self.screen_width = QApplication.primaryScreen().size().width()
        self.screen_height = QApplication.primaryScreen().size().height()

        layout = QVBoxLayout()

        self.width_label = QLabelWidget(f"최대 너비 (현재: {parent.max_width}, 최대: {self.screen_width})")
        self.width_input = QLineEdit(str(parent.max_width))
        layout.addWidget(self.width_label)
        layout.addWidget(self.width_input)

        self.height_label = QLabelWidget(f"최대 높이 (현재: {parent.max_height}, 최대: {self.screen_height})")
        self.height_input = QLineEdit(str(parent.max_height))
        layout.addWidget(self.height_label)
        layout.addWidget(self.height_input)

        self.apply_button = QPushButton("적용")
        self.apply_button.clicked.connect(self.apply_settings)
        layout.addWidget(self.apply_button)

        self.setLayout(layout)

    def apply_settings(self):
        try:
            new_width = int(self.width_input.text())
            new_height = int(self.height_input.text())

            if new_width <= 0 or new_height <= 0:
                raise ValueError

            if new_width > self.screen_width:
                QMessageBox.warning(self, "경고", f"최대 너비는 {self.screen_width} 까지 가능합니다.")
                new_width = self.screen_width

            if new_height > self.screen_height:
                QMessageBox.warning(self, "경고", f"최대 높이는 {self.screen_height} 까지 가능합니다.")
                new_height = self.screen_height

            self.parent.max_width = new_width
            self.parent.max_height = new_height
            self.parent.save_config_settings()

            self.width_label.setText(f"최대 너비 (현재: {new_width}, 최대: {self.screen_width})")
            self.height_label.setText(f"최대 높이 (현재: {new_height}, 최대: {self.screen_height})")

            if self.parent.image_path and os.path.exists(self.parent.image_path):
                self.parent.load_image(self.parent.image_path)

            self.close()

        except ValueError:
            QMessageBox.warning(self, "오류", "올바른 숫자를 입력하세요.")

class OverlayWindow(QLabel):
    def __init__(self):
        super().__init__()

        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.movie = None
        self.drag_position = None

        self.max_width = DEFAULT_MAX_WIDTH
        self.max_height = DEFAULT_MAX_HEIGHT
        self.image_path = None

        self.load_config_settings()

        if self.image_path and os.path.exists(self.image_path):
            self.load_image(self.image_path)

        self.show()

    def load_image(self, path):
        if path.lower().endswith(".gif"):
            if self.movie:
                self.movie.stop()
                self.movie.deleteLater()

            self.movie = QMovie(path)
            if not self.movie.isValid():
                QMessageBox.warning(self, "오류", f"GIF 파일 로드 실패: {path}")
                return

            self.movie.jumpToFrame(0)
            orig_size = self.movie.currentPixmap().size()
            new_size = self.limit_size(orig_size)

            self.movie.setScaledSize(new_size)
            self.setMovie(self.movie)
            self.movie.start()

            self.resize_window_to_image(new_size)

        else:
            if self.movie:
                self.movie.stop()
                self.movie.deleteLater()
                self.movie = None

            pixmap = QPixmap(path)
            if pixmap.isNull():
                QMessageBox.warning(self, "오류", f"이미지 로드 실패: {path}")
                return

            new_size = self.limit_size(pixmap.size())
            scaled_pixmap = pixmap.scaled(new_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.setPixmap(scaled_pixmap)

            self.resize_window_to_image(new_size)

    def limit_size(self, size: QSize):
        width, height = size.width(), size.height()

        if width <= self.max_width and height <= self.max_height:
            return size

        width_ratio = self.max_width / width
        height_ratio = self.max_height / height
        scale_ratio = min(width_ratio, height_ratio)

        new_width = int(width * scale_ratio)
        new_height = int(height * scale_ratio)

        return QSize(new_width, new_height)

    def resize_window_to_image(self, size: QSize):
        self.setFixedSize(size)
        self.resize(size)

    def load_config_settings(self):
        if not os.path.exists(CONFIG_FILE):
            return
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("Image="):
                    self.image_path = line.strip().split("=", 1)[1]
                elif line.startswith("MaxWidth="):
                    self.max_width = int(line.strip().split("=", 1)[1])
                elif line.startswith("MaxHeight="):
                    self.max_height = int(line.strip().split("=", 1)[1])

    def save_config_settings(self):
        lines = []
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                lines = f.readlines()

        found_image = False
        found_width = False
        found_height = False

        for i, line in enumerate(lines):
            if line.startswith("Image="):
                lines[i] = f"Image={self.image_path}\n"
                found_image = True
            elif line.startswith("MaxWidth="):
                lines[i] = f"MaxWidth={self.max_width}\n"
                found_width = True
            elif line.startswith("MaxHeight="):
                lines[i] = f"MaxHeight={self.max_height}\n"
                found_height = True

        if not found_image and self.image_path:
            lines.append(f"Image={self.image_path}\n")
        if not found_width:
            lines.append(f"MaxWidth={self.max_width}\n")
        if not found_height:
            lines.append(f"MaxHeight={self.max_height}\n")

        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            f.writelines(lines)

    def contextMenuEvent(self, event):
        menu = QMenu(self)

        load_action = menu.addAction("사진 불러오기")
        option_action = menu.addAction("설정")
        quit_action = menu.addAction("종료")

        action = menu.exec_(self.mapToGlobal(event.pos()))

        if action == load_action:
            file_path, _ = QFileDialog.getOpenFileName(self, "이미지 선택", "", "이미지 파일 (*.png *.jpg *.jpeg *.gif)")
            if file_path:
                self.image_path = file_path
                self.load_image(file_path)
                self.save_config_settings()

        elif action == option_action:
            options_dialog = OptionsDialog(self)
            options_dialog.exec_()

        elif action == quit_action:
            self.close()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self.drag_position:
            self.move(event.globalPos() - self.drag_position)
            event.accept()

    def closeEvent(self, event):
        if self.movie:
            self.movie.stop()
            self.movie.deleteLater()
        self.deleteLater()
        QCoreApplication.quit()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    overlay = OverlayWindow()
    sys.exit(app.exec_())