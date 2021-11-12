import random
import sqlite3
import sys
import datetime as dt

from PyQt5.Qt import QUrl
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QFont, QPixmap, QIcon
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtWidgets import QApplication, QMainWindow, QInputDialog, \
    QFileDialog, QWidget

from design.about import Ui_Ui
from design.player import Ui_Form
from design.mainwindow import Ui_MainWindow
from design.sign import Ui_SighInForm


class Main(QMainWindow, Ui_MainWindow):  # Основное окно
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.pushButton.clicked.connect(self.check_password)
        self.pushButton_2.clicked.connect(self.sigh_in)

    def check_password(self):  # Проверка логина и пароля при входе
        connection = sqlite3.connect('audio.sqlite')
        cursor = connection.cursor()
        dictionary = {}
        for i, login, password in cursor.execute("""SELECT * FROM accounts""").fetchall():
            dictionary[login] = password
        connection.close()
        if self.lineEdit.text() not in dictionary.keys():
            self.label.setText("Wrong login")
        else:
            if dictionary[self.lineEdit.text()] != self.lineEdit_2.text():
                self.label.setText("Wrong password")
            else:
                self.player = MyWidget(self.lineEdit.text())
                self.player.show()

    def sigh_in(self):  # Переход на окно с регистрацией
        self.w = SighIn()
        self.w.show()


class SighIn(QWidget, Ui_SighInForm):  # Окно с регистрацией
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.pushButton.clicked.connect(self.check)
        self.connection = sqlite3.connect('audio.sqlite')
        self.cursor = self.connection.cursor()
        self.result = self.cursor.execute("""SELECT login, password FROM accounts""").fetchall()
        self.connection.close()

    def check(self):  # Проверка пароля при регистрации
        sequence = 'qwertyuiop asdfghjkl zxcvbnm йцукенгшщзхъ фывапролджэё ячсмитьбю'
        logins = [i[0] for i in self.result]
        password = self.lineEdit_2.text()
        if self.lineEdit.text() in logins:
            self.label_3.setText("Логин занят.")
        else:
            if len(password) < 9:
                self.label_3.setText("Длина пароля должна быть больше 9 символов.")
                return
            if password.isdigit() or password.isalpha():
                self.label_3.setText("Пароль должен соддержать хотя бы одну букву и цифру.")
                return
            if password.isupper() or password.islower():
                self.label_3.setText("Пароль должен соддержать буквы разного регистра.")
                return
            for i in range(len(password) - 2):
                if password[i: i + 3].lower() in sequence:
                    self.label_3.setText("Пароль не должен соддержать буквы находящиеся рядом.")
                    return
            for i in '1234567890':
                if i in password:
                    self.connection = sqlite3.connect('audio.sqlite')
                    self.cursor = self.connection.cursor()
                    self.cursor.execute("""INSERT INTO accounts(login, password) VALUES(?, ?)""",
                                        (self.lineEdit.text(), password,))
                    self.connection.commit()
                    self.connection.close()
                    self.close()
                    return
            self.label_3.setText("Ошибка.")


class MyWidget(QWidget, Ui_Form):  # Окно с плеером
    def __init__(self, login):
        super().__init__()
        self.setupUi(self)
        self.login = login
        self.pause_image = QPixmap("icons/pause.png")
        self.play_image = QPixmap("icons/play.png")
        self.next_image = QPixmap("icons/next.png")
        self.prev_image = QPixmap("icons/previous.png")
        self.repeating = QPixmap("icons/repeat-button.png")
        self.repeat_image = QPixmap("icons/repeating.png")
        self.shuffle_image = QPixmap("icons/shuffle.png")
        self.fullvolume = QPixmap("icons/fullvolume.png")
        self.lowvolume = QPixmap("icons/lowlvolume.png")
        self.novolume = QPixmap("icons/novolume.png")
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
        self.listWidget.itemDoubleClicked.connect(self.change_audio)
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
        self.listWidget_playlist.itemDoubleClicked.connect(self.change_playlist)
        self.addPlayListButton.clicked.connect(self.add_playlist)
        self.addToPlaylist.clicked.connect(self.add_to_playlist)
        self.stop_PlayButton.setShortcut('Space')
        self.nextButton.setShortcut('N')
        self.prevButton.setShortcut('B')
        self.toolButton.clicked.connect(self.about_program)
        self.onstart()

    def onstart(self):  # При старте программы инициализируется список аудио и комбобокс с плейлистами
        self.update_list()
        result = self.cursor.execute("""SELECT title FROM playlists WHERE login = ?""", (self.login,)).fetchall()
        for i in result:
            self.listWidget_playlist.addItem(i[0])

    def add_to_playlist(self):  # Добавление аудио в плейлист
        choice, ok_pressed = QInputDialog.getItem(
            self, "Выберите плейлист", "плейлист",
            ([i[1] for i in
              self.connection.execute("""SELECT * FROM playlists WHERE login = ?""", (self.login,)).fetchall()]), 1,
            False)
        if ok_pressed:
            self.cursor.execute("""INSERT INTO main_table(title, type, playlist, login) VALUES(?, ?, ?, ?)""", (
                self.listWidget.currentItem().text(), self.lst[self.listWidget.currentRow()][1], choice, self.login,))
            self.connection.commit()

    def add_playlist(self):  # Создание нового плейлиста
        inp, ok_pressed1 = QInputDialog.getText(self, "Введите название плейлиста",
                                                "название")
        if ok_pressed1:
            self.listWidget_playlist.addItem(inp)
            self.cursor.execute("""INSERT INTO playlists(title, login) VALUES(?, ?)""", (inp, self.login,))
            self.connection.commit()

    def change_playlist(self):  # Смена плейлиста
        self.currentplaylist = self.listWidget_playlist.currentItem().text()
        self.update_list()

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
                self.next_audio()

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
                    self.cursor.execute(
                        """INSERT INTO main_table(title, type, playlist, login) VALUES(?, 2, ?, login)""",
                        (fname, self.currentplaylist, self.login,))
                    self.connection.commit()
            else:
                inp, ok_pressed1 = QInputDialog.getText(self, "Введите ссылку",
                                                        "Ссылка на аудио файл")
                if ok_pressed1:
                    self.cursor.execute(
                        """INSERT INTO main_table(title, type, playlist, login) VALUES(?, 1, ?, login)""",
                        (inp, self.currentplaylist, self.login))
                    self.connection.commit()
        self.update_list()

    def change_audio(self):  # Смена аудио
        self.player.setMedia(QMediaContent(QUrl(
            self.listWidget.currentItem().text()
        )))
        self.from_start_label.setText("00:00")
        self.time = 0
        self.DurationSlider.setValue(0)
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

    def update_list(self):  # Инициализация списка аудио
        self.listWidget.clear()
        result = self.cursor.execute(
            f"SELECT * FROM main_table WHERE playlist = '{self.currentplaylist}' AND login = '{self.login}'").fetchall()
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

    def about_program(self):  # открытие окна с информацией
        self.about = AboutProgram()
        self.about.show()


def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)


class AboutProgram(QWidget, Ui_Ui):  # Окно с информацией о программе
    def __init__(self):
        super().__init__()
        self.setupUi(self)


QSS = """
QSlider::groove:horizontal {
    border-radius: 1px;       
    height: 7px;              
    margin: -1px 0;           
}
QSlider::handle:horizontal {
    background-color: rgb(85, 17, 255);
    border: 2px solid #ff0000;
    height: 14px;     
    width: 12px;
    margin: -4px 0;     
    border-radius: 7px  ;
    padding: -4px 0px;  
}
QSlider::add-page:horizontal {
    background: darkgray;
}
QSlider::sub-page:horizontal {
    background: #1abc9c;
}
"""
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(QSS)
    ex = Main()
    ex.show()
    sys.excepthook = except_hook
    sys.exit(app.exec())
