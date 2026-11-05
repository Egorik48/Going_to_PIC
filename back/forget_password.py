import sqlite3
import sys

from PyQt6.QtWidgets import QWidget, QApplication, QMessageBox

from ui.QForgetUI import QForgetUI


class Forget(QWidget, QForgetUI):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self.btn_received.clicked.connect(self.receive)
        self.go_enter.clicked.connect(self.go_enter)

    def receive(self):
        con = sqlite3.connect('users.sqlite')
        cur = con.cursor()
        user = cur.execute(f"""SELECT id FROM data_users WHERE secret = ?""", (self.lineEdit.text()))
        if not user:
            QMessageBox.warning(self, 'Ошибочка...', "У вас неправильный код, повторите ещё раз.")
            return
        cur.execute("""DELETE FROM data_users WHERE id = ?""", (user[0]))
        QMessageBox.information(self, 'Не нужно было терять пароль', "Мы удалили ваш аккаунт,"
                                                                     " в следующий раз не теряйте пароль")
        from register_dialog import RegisterWindow
        self.reg = RegisterWindow()
        self.reg.show()

        self.close()

    def go_enter(self):
        from login_window import LoginWindow

        self.login_window = LoginWindow()
        self.login_window.show()

        self.close()


def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    sys.excepthook = except_hook

    ex = Forget()
    ex.show()

    sys.exit(app.exec())