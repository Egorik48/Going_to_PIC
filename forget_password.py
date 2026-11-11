import sqlite3

from PyQt6.QtWidgets import QWidget, QMessageBox

from ui.QForgetUI import QForgetUI


class Forget(QWidget, QForgetUI):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self.btn_received.clicked.connect(self.receive)
        self.go_enter.clicked.connect(self.func_go_enter)

    def receive(self):
        """функция ищет пользователя с секретным ключом, который написал пользователь, если нашёл,
         то удаляет аккаунт, чтобы пользователь хорошо знал свой пароль в будущем"""
        from register_dialog import RegisterWindow

        con = sqlite3.connect('users.sqlite')
        cur = con.cursor()
        user = cur.execute(f"""SELECT id FROM data_users WHERE secret = ?""",
                           (self.lineEdit.text(),)).fetchone()
        if not user:
            QMessageBox.warning(self, 'Ошибочка...', "У вас неправильный код, повторите ещё раз.")
            con.close()
            return

        cur.execute("""DELETE
                       FROM data_users
                       WHERE id = ?""", (user[0],))
        QMessageBox.information(self, 'Не нужно было терять пароль', "Мы удалили ваш аккаунт,"
                                                                     " в следующий раз не теряйте пароль")
        con.commit()
        con.close()
        self.reg = RegisterWindow()
        self.reg.show()  # летим в окно регистрации

        self.close()

    def func_go_enter(self):
        from login_window import LoginWindow

        self.login_window = LoginWindow()
        self.login_window.show()  # летим в окно входа

        self.close()
