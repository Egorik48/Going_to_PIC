import random
import sys
import sqlite3

from PyQt6 import QtCore, QtMultimedia
from PyQt6.QtCore import QMimeData, Qt
from PyQt6.QtWidgets import QWidget, QApplication, QLineEdit, QMessageBox

from ui.QRegisterUI import QRegisterUI


class RegisterWindow(QWidget, QRegisterUI):
    def __init__(self, /):
        super().__init__()
        self.setupUi(self)
        self.password_first.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_second.setEchoMode(QLineEdit.EchoMode.Password)
        self.text_error.setStyleSheet("color: red;")
        self.text_error.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.media = QtCore.QUrl.fromLocalFile('end_reg.mp3')
        self.audio_output = QtMultimedia.QAudioOutput()
        self.audio_output.setVolume(1)
        self.player = QtMultimedia.QMediaPlayer()
        self.player.setAudioOutput(self.audio_output)
        self.player.setSource(self.media)

        self.btn_reg.clicked.connect(self.try_reg)
        self.btn_login.clicked.connect(self.go_login)

    def try_reg(self):
        if len(self.login.text()) < 5:
            self.text_error.setText('Логин должен иметь ≥ 5 символов!')
            return

        if self.password_first.text() != self.password_second.text():
            self.text_error.setText('Пароли не совпадают!')
            return

        if len(self.password_first.text()) < 7:
            self.text_error.setText('Пароль должен содержать ≥ 7 символов!')
            return

        if not any(i.isupper() for i in self.password_first.text()):
            self.text_error.setText('Пароль должен содержать ≥ 1 заглавную букву!')
            return

        if not any(i in '+=_-()<>&*$' for i in self.password_first.text()):
            self.text_error.setText('Пароль должен содержать ≥ 1 спец. символ! (+=_-()<>&*$)')
            return

        connection = sqlite3.connect('users.sqlite')
        cursor = connection.cursor()
        logins = cursor.execute('SELECT login FROM data_users').fetchall()
        logins = [row[0] for row in logins]

        if self.login.text() in logins:
            self.text_error.setText('Этот логин уже занят, поменяйте на другой.')
            return

        secret = random.sample('qwertyuiop[]asdfghjkl;zxcvbnm,./1'
                               '234567890-=ёйцукенгшщзъфывапролджэячсмитьбю.',
                               10)  # нужно сделать проверку в бд, что он уникальный
        secret = ''.join(secret)
        mime_data = QMimeData()
        mime_data.setText(secret)

        QApplication.clipboard().setMimeData(mime_data)

        cursor.execute(
            f"""INSERT INTO data_users (login, password, secret, active) 
            VALUES (?, ?, ?, (SELECT type FROM actives WHERE title == 'в главном окне'))""",
            (self.login.text(), self.password_first.text(), secret)
        )
        connection.commit()
        connection.close()

        self.player.play()
        self.text_error.setText('Получилось!')
        self.text_error.setStyleSheet('color: orange;')
        QMessageBox.information(self, 'Зарегались!', f'Ты успешно прошёл регистрацию,'
                                                     f' но если ты потеряешь пароль, то у тебя есть секретный ключ'
                                                     f' для восстановления, вот он: {secret}, не беспокойся, он уже у'
                                                     f' тебя в буфере обмена, сохрани его куда-нибудь.')
        from main_window import MainWindow
        self.main = MainWindow(self.login.text())
        self.main.show()

        self.close()

    def go_login(self):
        from login_window import LoginWindow

        self.login_window = LoginWindow()
        self.login_window.show()

        self.close()


def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    sys.excepthook = except_hook

    ex = RegisterWindow()
    ex.show()

    sys.exit(app.exec())
