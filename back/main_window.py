import random
import sqlite3
import string
import sys
import os
import filetype
import pathlib

from PyQt6.QtCore import QMimeData
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import QWidget, QFileDialog, QApplication, QMessageBox
from PIL import Image, UnidentifiedImageError

import math

from ui.QMainUI import QMainUI

russian_letters = 'АаБбВвГгДдЕеЁёЖжЗзИиЙйКкЛлМмНнОоПпРрСсТтУуФфХхЦцЧчШшЩщЪъЫыЬьЭэЮюЯя'
letters = string.ascii_letters + russian_letters


class MainWindow(QWidget, QMainUI):
    def __init__(self, us_login):
        super().__init__()
        self.us_login = us_login
        self.setupUi(self)
        self.f_name = ''
        self.curr_password = ''

        pixmap = QPixmap('fun_pic.jpg')
        self.pic_for_fun.setPixmap(pixmap)
        self.pic_for_fun.setScaledContents(True)

        self.btn_create.clicked.connect(self.create_pic)
        self.btn_attach.clicked.connect(self.attach)
        self.btn_copy.clicked.connect(self.share_it)
        self.btn_save.clicked.connect(self.save_image)
        self.btn_transcribe.clicked.connect(self.recognize)
        self.save_rec_file.clicked.connect(self.save_rec)

    def attach(self):
        self.f_name = QFileDialog.getOpenFileName(
            self, 'Выбрать файл', 'C:\\Users\\ser\\Downloads',
            'Все файлы (*);;Картинка (*.jpg);;Картинка (*.png);;')[0]
        if self.f_name:
            self.text_result.setText('Файл прикреплён!')
            self.text_result.setStyleSheet("color: green;")
            self.password.setText('')
            self.save_rec_file.setEnabled(False)
            self.label_file.setText(
                f'Прикреплённый файл: {(self.f_name.rsplit('/', 1)[-1]).rsplit('.', 1)[0][:20]
                                       + '....' + (self.f_name.rsplit('/', 1)[-1]).rsplit('.', 1)[1] if
                len((self.f_name.rsplit('/', 1)[-1]).rsplit('.', 1)[0]) > 20 else
                (self.f_name.rsplit('/', 1)[-1]).rsplit('.', 1)[0][:20]}'
                + '.' + (self.f_name.rsplit('/', 1)[-1]).rsplit('.', 1)[1]
            )

            try:
                img_for_show = Image.open(self.f_name)
                img_for_show.thumbnail((731, 1000), Image.Resampling.LANCZOS)
                img_for_show.save("thumbnail_pic.png")
                self.textBrowser.setHtml(f"""<img src="thumbnail_pic.png"/>""")
            except UnidentifiedImageError:
                self.textBrowser.setHtml(f"""<img src="img_for_show.png"/>""")
        return

    def create_pic(self):
        if not self.password.text():
            self.text_result.setText('Введите пароль для кодировки!')
            self.text_result.setStyleSheet("color: red;")
            return

        if len(self.password.text()) < 5:
            self.text_result.setText('Слишком короткий пароль! (нужно ≥ 5 символов)')
            self.text_result.setStyleSheet("color: red;")
            return

        if sum([int(i in letters) for i in self.password.text()]) < 3:
            self.text_result.setText('В пароле должно ≥ 3 буквы!')
            self.text_result.setStyleSheet("color: red;")
            return

        self.curr_password = self.password.text()  # нужен для копирования сохранённой картинки
        code = sum(list(map(lambda x: ord(x), self.password.text())))

        if self.radio_file.isChecked():
            if not self.f_name:
                self.text_result.setText('Сначала прикрепите файл!')
                self.text_result.setStyleSheet("color: red;")
                return

            with open(self.f_name, 'rb') as f:
                raw_byte = list(f.read())

        elif self.radio_text.isChecked():
            if not self.input_text.toPlainText().encode('utf-8').strip():
                self.text_result.setText('Нельзя зашифровать пустоту!')
                self.text_result.setStyleSheet("color: red;")
                return
            raw_byte = self.input_text.toPlainText().encode('utf-8')

        # Защита от ошибки (DecompressionBombWarning: Image size (n pixels) exceeds limit of 89478485 pixels,
        # could be decompression bomb DOS attack.)
        if 731 * math.ceil(len(raw_byte) / 731) > 89478485:
            QMessageBox.warning(self, 'Много!', 'У ваш файл весит слишком много,'
                                                ' просим прощёния за доставленные неудобства.'
                                                ' Прикрепите файл поменьше!')
            return

        create_im = Image.new('RGB', (731, y0 := math.ceil(len(raw_byte) / 731)), color='white')
        pixels = create_im.load()
        count_pix = 731 * y0

        c = 0
        for x in range(731):
            for y in range(y0):
                try:
                    pixels[x, y] = (random.randint(0, 255), (code - raw_byte[c]) % 256, (code - raw_byte[c]) // 256)
                except IndexError:
                    pixels[x, y] = (0, 0, 0)

                self.progress.setValue(int(round(c / count_pix, 2) * 100))
                c += 1
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
                if pixels[x, y] != (0, 0, 0):
                    raw_bytes.append(
                        code - ((pixels[x, y][2] * 256) + pixels[x, y][1])
                    )

        global type_file
        raw_bytes = bytes(raw_bytes)
        type_file = filetype.guess(raw_bytes).extension if filetype.guess(raw_bytes) else 'txt'

        try:
            with open(f'rec_im.{type_file}', 'wb') as f:
                f.write(raw_bytes)

            QMessageBox.information(self, "Ура!", "Расшифровали!")

            if type_file == 'txt':
                self.input_text.setPlainText(raw_bytes.decode('utf-8'))

            self.save_rec_file.setEnabled(True)

        except (ValueError, AttributeError, Exception):
            QMessageBox.information(self, "Что-то пошло не по плану...",
                                    "Убедитесь, что у вас правильный пароль или картинка")

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

    def save_rec(self):
        fname, _ = QFileDialog.getSaveFileName(
            self,
            'Сохранить файл',
            f'C://Users//user//Downloads//new_file.{type_file}',
            f'Разрешение (*.{type_file})'
        )

        if fname:
            dir, name = fname.rsplit('/', 1)
            os.rename(f'rec_im.{type_file}', name)
            file_from = pathlib.Path(name)
            file_to = pathlib.Path(dir)
            file_from.copy_into(file_to)
            self.text_result.setText('Сохранено!')
            self.text_result.setStyleSheet('color: violet;')

    def exit_on_db(self):
        con = sqlite3.connect('users.sqlite')
        cur = con.cursor()
        cur.execute(f"""UPDATE data_users
         SET active = (SELECT type FROM actives WHERE title == 'не в приложении')
         WHERE login = ?""", (self.us_login,))  # хз не знаю почему не работает
        con.commit()
        con.close()


def cleanup():
    remove_list = ['created_image.png', f'rec_im.{type_file}', 'thumbnail_pic.png']
    for item in remove_list:
        try:
            os.remove(item)
        except FileNotFoundError:
            pass


def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)



sys.excepthook = except_hook
