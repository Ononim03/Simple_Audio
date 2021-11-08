import random
import sqlite3
import sys
from PyQt5.Qt import QUrl
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QFont, QPixmap, QIcon
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent, QMediaPlaylist
from PyQt5.QtWidgets import QApplication, QMainWindow, QInputDialog, \
    QFileDialog
import datetime as dt
from untitled import Ui_MainWindow


class MyWidget(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.pause_image = QPixmap("pause.png")
        self.play_image = QPixmap("play.png")
        self.next_image = QPixmap("right-arrow.png")
        self.prev_image = QPixmap("left-arrow.png")
        self.repeating = QPixmap("repeat-button.png")
        self.repeat_image = QPixmap("repeating.png")
        self.shuffle_image = QPixmap("shuffle.png")
        self.fullvolume = QPixmap("fullvolume.png")
        self.lowvolume = QPixmap("lowlvolume.png")
        self.novolume = QPixmap("novolume.png")
        self.randomButton.setIcon(QIcon(self.shuffle_image))
        self.infButton.setIcon(QIcon(self.repeat_image))
        self.prevButton.setIcon(QIcon(self.prev_image))
        self.nextButton.setIcon(QIcon(self.next_image))
        self.infButton.clicked.connect(self.repeat)
        self.randomButton.clicked.connect(self.shuffle)
        custom_font = QFont()
        custom_font.setPointSize(10)
        self.stop_PlayButton.setIcon(QIcon(self.play_image))
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
        self.currentplaylist = "Без плейлиста"
        self.is_repeating = False
        self.stop_PlayButton.setToolTip("Play")
        self.DurationSlider.valueChanged.connect(self.rewind_to_duration)
        self.current_time = self.DurationSlider.value()
        self.listWidget.clicked.connect(self.change_audio)
        self.nextButton.clicked.connect(self.next_audio)
        self.prevButton.clicked.connect(self.prev_audio)
        self.player.durationChanged.connect(self.change_duration)
        self.timer = QTimer()
        self.timer.setInterval(1000)
        self.time = 0
        self.nextButton.setToolTip("Next")
        self.prevButton.setToolTip("Previous")
        self.duration = 0
        self.timer.timeout.connect(self.showtime)
        self.changePlaylistBox.currentTextChanged.connect(self.change_playlist)
        self.addPlayListButton.clicked.connect(self.add_playlist)
        self.addToPlaylist.clicked.connect(self.add_to_playlist)
        self.onstart()

    def onstart(self):  # При старте программы инициализируется список аудио и комбобокс с плейлистами
        self.updateList()
        result = self.cursor.execute("""SELECT title FROM playlists""").fetchall()
        for i in result:
            self.changePlaylistBox.addItem(i[0])

    def add_to_playlist(self):  # Добавление аудио в плейлист
        choice, ok_pressed = QInputDialog.getItem(
            self, "Выберите плейлист", "плейлист",
            ([self.changePlaylistBox.itemText(i) for i in range(self.changePlaylistBox.count())]), 1, False)
        if ok_pressed:
            self.cursor.execute("""INSERT INTO main_table(title, type, playlist) VALUES(?, ?, ?)""", (
                self.listWidget.currentItem().text(), self.lst[self.listWidget.currentRow()][1], choice,))
            self.connection.commit()

    def add_playlist(self):  # Создание нового плейлиста
        inp, ok_pressed1 = QInputDialog.getText(self, "Введите название плейлиста",
                                                "название")
        if ok_pressed1:
            self.changePlaylistBox.addItem(inp)
            self.cursor.execute("""INSERT INTO playlists(title) VALUES(?)""", (inp,))
            self.connection.commit()

    def change_playlist(self):  # Смена плейлиста
        self.currentplaylist = self.changePlaylistBox.currentText()
        self.updateList()

    def showtime(self):  # Таймер
        time = dt.timedelta(seconds=self.time)
        self.from_start_label.setText(f"{time.seconds // 60:02d}:{time.seconds % 60:02d}")
        self.time += 1
        self.DurationSlider.setValue(round(self.time * 1000))
        if self.time * 1000 == self.duration:
            self.from_start_label.setText("00:00")
            self.timer.stop()
            self.time = 0
            self.DurationSlider.setValue(0)
            if self.is_repeating:
                self.play_media()
                self.timer.start()
            else:
                self.pause_media()

    def prev_audio(self):  # Переключение на предыдущее аудио
        if self.listWidget.currentRow() == 0:
            self.listWidget.setCurrentRow(len(self.lst) - 1)
        else:
            self.listWidget.setCurrentRow(self.listWidget.currentRow() - 1)
        self.change_audio()
        self.pause_media()

    def next_audio(self):  # Переключение на следующее аудио
        if self.listWidget.currentRow() + 2 > len(self.lst):
            self.listWidget.setCurrentRow(0)
        else:
            self.listWidget.setCurrentRow(self.listWidget.currentRow() + 1)
        self.change_audio()
        self.pause_media()

    def show_dialog(self):  # Добавление аудио в список
        choice, ok_pressed = QInputDialog.getItem(
            self, "Выберите вид аудио", "Какой формат файла?",
            ("Ссылка", "Файл"), 1, False)
        if ok_pressed:
            if choice == 'Файл':
                fname = QFileDialog.getOpenFileName(self, 'Выбрать аудио', '')[0]
                if fname:
                    self.cursor.execute("""INSERT INTO main_table(title, type, playlist) VALUES(?, 2, ?)""",
                                        (fname, self.currentplaylist))
                    self.connection.commit()
            else:
                inp, ok_pressed1 = QInputDialog.getText(self, "Введите ссылку",
                                                        "Ссылка на аудио файл")
                if ok_pressed1:
                    self.cursor.execute("""INSERT INTO main_table(title, type, playlist) VALUES(?, 1 ?)""",
                                        (inp, self.currentplaylist))
                    self.connection.commit()
        self.updateList()

    def change_audio(self):  # Смена аудио
        if self.lst[self.listWidget.currentRow()][1] == 1:
            self.player.setMedia(QMediaContent(QUrl(
                self.listWidget.currentItem().text()
            )))
        else:
            self.player.setMedia(QMediaContent(QUrl.fromLocalFile(self.listWidget.currentItem().text())))
        self.from_start_label.setText("00:00")
        self.time = 0
        self.timer.stop()
        self.pause_media()

    def change_volume(self, value):  # Настройка громкости
        self.player.setVolume(value)
        if value > 70:
            self.label.setPixmap(self.fullvolume)
        elif value != 0:
            self.label.setPixmap(self.lowvolume)
        elif value == 0:
            self.label.setPixmap(self.novolume)

    def run(self):  # Проигрывание аудио
        if self.playing:
            self.stop_PlayButton.setToolTip("Play")
            self.pause_media()
        else:
            self.stop_PlayButton.setToolTip("Pause")
            self.play_media()

    def play_media(self):
        self.player.play()
        self.stop_PlayButton.setIcon(QIcon(self.pause_image))
        self.playing = True
        self.timer.start()

    def pause_media(self):
        self.timer.stop()
        self.player.pause()
        self.stop_PlayButton.setIcon(QIcon(self.play_image))
        self.playing = False

    def change_duration(self, value):  # Перемотка аудио
        self.duration = value
        self.DurationSlider.setMaximum(value)
        time = dt.timedelta(milliseconds=value)
        self.duration_label.setText(f"{time.seconds // 60:02d}:{time.seconds % 60:02d}")

    def closeEvent(self, event):  # Отключение от БД
        self.connection.close()

    def updateList(self):  # Инициализация списка аудио
        self.listWidget.clear()
        result = self.cursor.execute(
            f"SELECT * FROM main_table WHERE playlist = '{self.currentplaylist}'").fetchall()
        self.lst = [(i[1], i[2]) for i in result]
        for i in self.lst:
            self.listWidget.addItem(i[0])

    def rewind_to_duration(self, pos):  # Реализация перемотки
        self.player.setPosition(pos)
        self.time = pos / 1000

    def repeat(self):  # Повтор
        if self.is_repeating:
            self.is_repeating = False
            self.infButton.setIcon(QIcon(self.repeat_image))
        else:
            self.is_repeating = True
            self.infButton.setIcon(QIcon(self.repeating))

    def shuffle(self):  # Перемешка
        self.listWidget.setCurrentRow(random.randint(0, len(self.lst) - 1))
        self.change_audio()


def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = MyWidget()
    ex.show()
    sys.excepthook = except_hook
    sys.exit(app.exec())
