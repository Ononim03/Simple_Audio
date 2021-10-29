import sqlite3
import sys

from PyQt5.Qt import QUrl
from PyQt5.QtGui import QFont
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtWidgets import QApplication, QMainWindow, QInputDialog, \
    QFileDialog

from untitled import Ui_MainWindow


class MyWidget(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        custom_font = QFont()
        custom_font.setPointSize(10)
        QApplication.setFont(custom_font, "QLabel")
        self.player = QMediaPlayer(self)
        self.playing = False
        self.addButton.clicked.connect(self.show_dialog)
        self.stop_PlayButton.clicked.connect(self.run)
        self.VolumeSlider.valueChanged.connect(self.change_volume)
        self.VolumeSlider.setValue(100)
        self.volume = self.VolumeSlider.value()
        self.connection = sqlite3.connect('audio.sqlite')
        self.cursor = self.connection.cursor()
        self.result = self.cursor.execute("""SELECT * FROM main_table""").fetchall()
        for i in self.result:
            self.listWidget.addItem(i[1])
        self.DurationSlider.valueChanged.connect(self.change_duration)
        self.current_time = self.DurationSlider.value()
        self.SpeedSlider.valueChanged.connect(self.change_speed)
        self.SpeedSlider.setValue(50)
        self.speed = self.SpeedSlider.value()
        self.listWidget.clicked.connect(self.change_audio)

    def show_dialog(self):
        choice, ok_pressed = QInputDialog.getItem(
            self, "Выберите вид аудио", "Какой формат файла?",
            ("Ссылка", "Файл"), 1, False)
        if ok_pressed:
            if choice == 'Файл':
                fname = QFileDialog.getOpenFileName(self, 'Выбрать аудио', '')[0]
            else:
                inp, ok_pressed1 = QInputDialog.getText(self, "Введите ссылку",
                                                        "Ссылка на аудио файл")
                if ok_pressed1:
                    pass

    def change_audio(self):
        self.player.setMedia(QMediaContent(QUrl(
            self.listWidget.currentItem().text()
        )))

    def change_volume(self, value):
        self.player.setVolume(value)

    def change_duration(self, value):
        pass

    def change_speed(self, value):
        pass

    def run(self):
        if self.playing:
            self.pause_media()
        else:
            self.play_media()

    def play_media(self):
        self.player.play()
        self.stop_PlayButton.setText('Pause')
        self.playing = True

    def pause_media(self):
        self.player.pause()
        self.stop_PlayButton.setText('Play')
        self.playing = False


def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = MyWidget()
    ex.show()
    sys.excepthook = except_hook
    sys.exit(app.exec())
