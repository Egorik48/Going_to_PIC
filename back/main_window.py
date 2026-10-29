import random
import sys

from PyQt6.QtWidgets import QWidget, QFileDialog, QApplication
from PIL import Image

import math

from web.QMainUI import QMainUI


class MAIN_WINDOW(QWidget, QMainUI):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.f_name = ''

        self.btn_create.clicked.connect(self.create_pic)
        self.btn_attach.clicked.connect(self.attach)

    def attach(self):
        self.f_name = QFileDialog.getOpenFileName(
            self, 'Выбрать картинку', '',
            'Картинка (*.jpg);;Картинка (*.png);;Все файлы (*)')[0]
        self.text_result.setText('Файл прикреплён!')
        self.text_result.setStyleSheet("color: green;")

    def create_pic(self):
        if not self.f_name:
            self.text_result.setText('Сначала прикрепите картинку!')
            self.text_result.setStyleSheet("color: red;")
            return

        if not self.password.text():
            self.text_result.setText('Введите пароль для кодировки!')
            self.text_result.setStyleSheet("color: red;")
            return

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
                    pixels[x, y] = (random.randint(0, 255), (code - raw_byte[c]) // 256, (code - raw_byte[c]) // 256)
                    c += 1
                except Exception:
                    pixels[x, y] = (0, 0, 0)
        create_im.save('created_image.png')
        self.text_result.setText('Файл зашифрован!')
        self.text_result.setStyleSheet("color: violet;")

        self.textBrowser.setHtml("""<img src="created_image.png"/>""")
        return

def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    sys.excepthook = except_hook
    ex = MAIN_WINDOW()
    ex.show()
    sys.exit(app.exec())
