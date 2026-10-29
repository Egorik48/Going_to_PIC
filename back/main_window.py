import random
import sys
import os
import filetype

from PyQt6.QtCore import QMimeData
from PyQt6.QtGui import QImage
from PyQt6.QtWidgets import QWidget, QFileDialog, QApplication, QMessageBox
from PIL import Image

import math

from web.QMainUI import QMainUI


class MAIN_WINDOW(QWidget, QMainUI):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.f_name = ''
        self.curr_password = ''

        self.btn_create.clicked.connect(self.create_pic)
        self.btn_attach.clicked.connect(self.attach)
        self.btn_copy.clicked.connect(self.share_it)
        self.btn_save.clicked.connect(self.save_image)
        self.btn_transcribe.clicked.connect(self.recognize)

    def attach(self):
        self.f_name = QFileDialog.getOpenFileName(
            self, 'Выбрать файл', '',
            'Все файлы (*);;Картинка (*.jpg);;Картинка (*.png);;')[0]
        if self.f_name:
            self.text_result.setText('Файл прикреплён!')
            self.text_result.setStyleSheet("color: green;")
            self.password.setText('')
        return

    def create_pic(self):
        if not self.f_name:
            self.text_result.setText('Сначала прикрепите картинку!')
            self.text_result.setStyleSheet("color: red;")
            return

        if not self.password.text():
            self.text_result.setText('Введите пароль для кодировки!')
            self.text_result.setStyleSheet("color: red;")
            return

        self.curr_password = self.password.text() # нужен для копирования сохранённой картинки
        code = sum(list(map(lambda x: ord(x), self.password.text())))

        with open(self.f_name, 'rb') as f:
            raw_byte = list(f.read())
            f.close()

        create_im = Image.new('RGB', (731, y0 := math.ceil(len(raw_byte) / 731)), color='white')
        pixels = create_im.load()
        c = 0
        for x in range(731):
            for y in range(y0):
                try:
                    pixels[x, y] = (random.randint(0, 255), (code - raw_byte[c]) % 256, (code - raw_byte[c]) // 256)
                    c += 1
                except IndexError:
                    pixels[x, y] = (0, 0, 0)
        create_im.save('created_image.png')
        self.text_result.setText('Файл зашифрован!')
        self.text_result.setStyleSheet("color: violet;")

        self.textBrowser.setHtml("""<img src="created_image.png"/>""")
        QMessageBox.information(self, "Ура!", "Картинка создана!")
        return

    def check_im(self, image):
        if image.isNull():
            self.text_result.setText('Сначала создайте картинку!')
            self.text_result.setStyleSheet('color: red;')
            return False
        return True

    def share_it(self):
        image = QImage('created_image.png')

        if not self.check_im(image):
            return

        mime_data = QMimeData()
        mime_data.setImageData(image)
        mime_data.setText(self.curr_password)

        QApplication.clipboard().setMimeData(mime_data)

        self.text_result.setText('Картинка и пароль скопированы!')
        self.text_result.setStyleSheet('color: orange;')

    def recognize(self):
        if not self.f_name:
            self.text_result.setText('Сначала прикрепите картинку!')
            self.text_result.setStyleSheet("color: red;")
            return

        if not self.f_name.endswith('.png'):
            self.text_result.setText('Неправильный формат картинки! Прикрепи .png!')
            self.text_result.setStyleSheet("color: red;")
            return

        if not self.password.text():
            self.text_result.setText('Введите пароль для кодировки!')
            self.text_result.setStyleSheet("color: red;")
            return

        image = Image.open(self.f_name)
        pixels = image.load()
        raw_bytes = []
        x0, y0 = image.size
        code = sum(list(map(lambda x: ord(x), self.password.text())))
        for x in range(x0):
            for y in range(y0):
                if  pixels[x, y] != (0, 0, 0):
                    raw_bytes.append(
                        code - ((pixels[x, y][2] * 256) + pixels[x, y][1])
                    )

        global type_file

        try:
            raw_bytes = bytes(raw_bytes)
            type_file = filetype.guess(raw_bytes).extension
            with open(f'rec_im.{type_file}', 'wb') as f:
                f.write(raw_bytes)
                f.close()
            QMessageBox.information(self, "Ура!", "Получилось!")
        except ValueError:
            QMessageBox.information(self, "Что-то пошло не по плану...", "Убедитесь, что у вас правильный пароль или картинка")






    def save_image(self):
        image = QImage('created_image.png')
        if not self.check_im(image):
            return

        fname, _ = QFileDialog.getSaveFileName(
            self,
            'Сохранить картинку',
            'created_image.png',
            'PNG (*.png)'
        )

        if fname:
            image.save(fname)
            self.text_result.setText('Картинка сохранена!')
            self.text_result.setStyleSheet('color: violet;')




def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)


def cleanup():
    try:
        os.remove('created_image.png')
        os.remove(f'rec_im.{type_file}')
    except FileNotFoundError:
        pass



if __name__ == '__main__':
    app = QApplication(sys.argv)
    sys.excepthook = except_hook

    app.aboutToQuit.connect(cleanup)

    ex = MAIN_WINDOW()
    ex.show()

    sys.exit(app.exec())


