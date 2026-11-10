import sqlite3
import sys

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QMessageBox, QLineEdit

from ui.QLoginUI import QLoginUI


class LoginWindow(QWidget, QLoginUI):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self.text_error.setStyleSheet('color: red')
        self.text_error.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.password.setEchoMode(QLineEdit.EchoMode.Password)

        self.btn_enter.clicked.connect(self.try_enter)
        self.btn_reg.clicked.connect(self.go_register)
        self.btn_forget_password.clicked.connect(self.forget)

    def try_enter(self):
        con = sqlite3.connect('users.sqlite')
        cur = con.cursor()
        user_id = cur.execute(f"""
        SELECT id 
        FROM data_users
        WHERE login = ? AND password = ?""",
                              (self.login.text(), self.password.text())).fetchone()

        if not user_id:
            self.text_error.setText('Неверный логин или пароль!')
            return

        self.text_error.setText('')
        QMessageBox.information(self, 'Успех!', 'Добро пожаловать!')

        from main_window import MainWindow
        import main_window as mw
        self.main = MainWindow(self.login.text())
        self.main.show()
        self.close()
        self.main.exit_on_db()
        mw.cleanup()



    def go_register(self):
        from register_dialog import RegisterWindow
        self.reg_wind = RegisterWindow()
        self.reg_wind.show()

        self.close()

    def forget(self):
        from forget_password import Forget
        self.forget = Forget()
        self.forget.show()

        self.close()



def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)



sys.excepthook = except_hook
