import datetime
import random
import sqlite3
import string
import os
import subprocess
import sys

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
        self.pic_for_fun.setPixmap(pixmap)  # прикрепляем весёлую картинку
        self.pic_for_fun.setScaledContents(True)

        self.btn_create.clicked.connect(self.create_pic)
        self.btn_attach.clicked.connect(self.attach)
        self.btn_copy.clicked.connect(self.share_it)
        self.btn_save.clicked.connect(self.save_image)
        self.btn_transcribe.clicked.connect(self.recognize)
        self.save_rec_file.clicked.connect(self.save_rec)
        self.btn_exit_from_account.clicked.connect(self.exit_from_account)

        self.btn_copy.setEnabled(False)

    def attach(self):
        """Функция выбора файла:
        Пользователь выбирает файл в QFileDialog и мы это запоминаем.
         Также выводится название файла, который он выбрал"""
        self.f_name = QFileDialog.getOpenFileName(
            self, 'Выбрать файл', str(pathlib.Path.home() / 'Downloads'),
            'Все файлы (*);;Картинка (*.jpg);;Картинка (*.png);;')[0]
        if self.f_name:
            self.text_result.setText('Файл прикреплён!')
            self.text_result.setStyleSheet("color: green;")
            self.password.setText('')
            self.save_rec_file.setEnabled(False)
            path = pathlib.Path(self.f_name)
            if len(path.stem) > 20:
                display_name = path.stem[:20] + '....' + path.suffix
            else:
                display_name = path.name
            self.label_file.setText(
                f'Прикреплённый файл: {display_name}')  # если название файла больше 20 символов, то мы обрезаем его (...)
            self.attach_file()  # ведёт заметку в бд

            # если это фотка, то сжимаем её и передаём на общее обозрение, иначе у мы выводим img_for_show.png
            try:
                img_for_show = Image.open(self.f_name)
                img_for_show.thumbnail((731, 1000), Image.Resampling.LANCZOS)
                img_for_show.save("thumbnail_pic.png")
                self.textBrowser.setHtml(f"""<img src="thumbnail_pic.png"/>""")
            except UnidentifiedImageError:
                self.textBrowser.setHtml(f"""<img src="img_for_show.png"/>""")
            except (OSError, Image.DecompressionBombError) as e:
                QMessageBox.warning(self, 'Ошибка изображения', f'Не удалось открыть изображение: {e}')
        return

    def create_pic(self):
        """Одна из главных функций в нашей программе, мы читаем байты переданного файла (или текста) и
        шифруем их с помощью алгоритма в пиксели"""
        self.btn_copy.setEnabled(False)

        if not self.check_passw():
            return

        if len(self.password.text()) < 5:
            self.text_result.setText('Слишком короткий пароль! (нужно ≥ 5 символов (буквы и цифры))')
            self.text_result.setStyleSheet("color: red;")
            return

        if not all(i in letters + string.digits for i in self.password.text()):
            self.text_result.setText('В пароле должны быть только буквы и цифры!')
            self.text_result.setStyleSheet("color: red;")
            return

        if sum([int(i in letters) for i in self.password.text()]) < 3:
            self.text_result.setText('В пароле должно ≥ 3 буквы!')
            self.text_result.setStyleSheet("color: red;")
            return

        if 30 < len(self.password.text()):
            self.text_result.setText('Пароль слишком большой! Он должен быть < 30.')
            self.text_result.setStyleSheet("color: red;")
            return

        self.curr_password = self.password.text()  # нужен для копирования сохранённой картинки
        code = sum(list(map(lambda x: ord(x), self.password.text())))  # преобразовываем пароль в числовое значение
        # с помощью ord(x), главное, чтобы наш пароль был > 255, поэтому у нас стоят такие ограничения

        if self.radio_file.isChecked():  # если пользователь выбрал шифрование файла
            if not self.f_name:  # если он ничего не прикрепил
                self.text_result.setText('Сначала прикрепите файл!')
                self.text_result.setStyleSheet("color: red;")
                return

            with open(self.f_name, 'rb') as f:  # читаем файл по байтово
                raw_byte = f.read()

            if not raw_byte:
                self.text_result.setText('Нельзя зашифровать пустой файл!')
                self.text_result.setStyleSheet('color: red;')
                return

        elif self.radio_text.isChecked():  # если пользователь выбрал шифрование текста
            if not self.input_text.toPlainText().encode('utf-8').strip():  # если он ничего не написал
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

        # создаем будущую зашифрованную картинку x = 731, потому что в геометрии textbrowzer,
        # куда мы будем выводить изображение, x = 731. y мы подстраиваем под количество сырых байтов / 731
        # округляем в большую сторону, чтобы всё вместилось
        create_im = Image.new('RGB', (731, y0 := math.ceil(len(raw_byte) / 731)), color='white')
        pixels = create_im.load()
        count_pix = 731 * y0

        # редактируем каждый пиксель
        c = 0
        for x in range(731):
            for y in range(y0):
                try:
                    # берём пиксель, значение красного канала - любое (точнее рандомное)
                    # зелёный - это остаток от деления числа 256 на разность числового значения нашего пароля и байта
                    # синий - это целочисленное деления числа 256 на разность числового значения нашего пароля и байта
                    # мы делаем это так как благодаря знанию пароля мы сможем узнать значение сырого байта, так как
                    # (code - raw_byte[c]) % 256 + (code - raw_byte[c]) // 256) * 256 = code - raw_byte[c]
                    pixels[x, y] = (random.randint(0, 255), (code - raw_byte[c]) % 256, (code - raw_byte[c]) // 256)
                except IndexError:
                    pixels[x, y] = (0, 0, 0)  # когда заканчиваются байты мы рисуем чёрным

                self.progress.setValue(int(round(c / count_pix, 2) * 100))  # двигаем progress bar
                c += 1
        create_im.save('created_image.png')

        if self.radio_text.isChecked():  # если пользователь шифровал текст
            self.text_result.setText('Текст зашифрован!')
            self.encrypt_text()  # делаем заметку в бд
        else:  # иначе, он шифровал файл
            self.text_result.setText('Файл зашифрован!')
            self.encrypt_file()  # делаем заметку в бд

        self.text_result.setStyleSheet("color: violet;")

        self.textBrowser.setHtml("""<img src="created_image.png"/>""")  # прикрепляем результат на обозрение
        QMessageBox.information(self, "Ура!", "Картинка создана!")
        self.btn_copy.setEnabled(True)
        return

    def check_im(self, image):  # проверка на созданную картинку
        if image.isNull():
            self.text_result.setText('Сначала создайте картинку!')
            self.text_result.setStyleSheet('color: red;')
            return False
        return True

    def share_it(self):
        """Метод копирует зашифрованную картинку и пароль у пользователя в буфер обмена"""
        image = QImage('created_image.png')

        if not self.check_im(image):
            return

        mime_data = QMimeData()  # знакомьтесь, тот, кто поможет запихнуть картинку и пароль в буфер обмена
        mime_data.setImageData(image)
        mime_data.setText(self.curr_password)

        QApplication.clipboard().setMimeData(mime_data)  # занесли в буфер

        self.text_result.setText('Картинка и пароль скопированы!')
        self.text_result.setStyleSheet('color: orange;')

    def check_passw(self):
        if not self.password.text():
            self.text_result.setText('Введите пароль для кодировки!')
            self.text_result.setStyleSheet("color: red;")
            return False
        return True

    def recognize(self):
        """Функция расшифровки изображения """
        self.save_rec_file.setEnabled(False)

        if not self.check_passw():
            return

        if not self.f_name:
            self.text_result.setText('Сначала прикрепите картинку!')
            self.text_result.setStyleSheet("color: red;")
            return False

        if not self.f_name.endswith('.png'):
            self.text_result.setText('Неправильный формат картинки! Прикрепи .png!')
            self.text_result.setStyleSheet("color: red;")
            return False

        image = Image.open(self.f_name)
        image = image.convert('RGB')

        if image.width != 731:
            QMessageBox.warning(self, 'Ошибка', 'Неправильный формат зашифрованной картинки!')
            return

        pixels = image.load()  # загружаем картинку
        raw_bytes = []
        x0, y0 = image.size  # получаем x, y, вскоре будем их исследовать
        code = sum(list(map(lambda x: ord(x), self.password.text())))  # получаем числовое значение через ord(x)
        for x in range(x0):
            for y in range(y0):
                if pixels[x, y] != (0, 0, 0):
                    raw_bytes.append(
                        code - ((pixels[x, y][2] * 256) + pixels[x, y][1])
                    )  # получаем сырой байт (было объяснение в create_pic)

        global type_file  # создаём глобальную переменную, которая будет узнавать формат файла
        try:
            raw_bytes = bytes(raw_bytes)  # преобразовываем числовое значение в сырые байты
            # узнаём формат файла, если не получается, то это .txt
            type_file = filetype.guess(raw_bytes).extension if filetype.guess(raw_bytes) else 'txt'
            with open(f'rec_im.{type_file}', 'wb') as f:  # записываем получившееся
                f.write(raw_bytes)

            QMessageBox.information(self, "Ура!", "Расшифровали!")

            if type_file == 'txt':  # если txt, то выводим на экран
                self.input_text.setPlainText(raw_bytes.decode('utf-8'))
                self.deciphered_text()  # делаем заметку в бд
            else:
                self.deciphered_file()  # делаем заметку в бд

            self.save_rec_file.setEnabled(True)  # включаем кнопку для сохранения получившегося фалйа

        except (ValueError, AttributeError, Exception) as e:
            print(e)
            QMessageBox.warning(self, "Что-то пошло не по плану...",
                                "Убедитесь, что у вас правильный пароль или картинка")

    def save_image(self):
        """Сохраняем зашифрованную картинку в формате .png (только в этом формате)"""
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

            if not image.save(fname, 'PNG'):
                QMessageBox.warning(
                    self,
                    'Ошибка',
                    'Не удалось сохранить изображение!'
                )
                return

            self.text_result.setText('Картинка сохранена!')
            self.text_result.setStyleSheet('color: violet;')
            self.save_file()

    def save_rec(self):
        """Сохраняем расшифрованный файл в формате, который у нас есть"""
        fname, _ = QFileDialog.getSaveFileName(
            self,
            'Сохранить файл',
            f'C://Users//user//Downloads//new_file.{type_file}',
            f'Разрешение (*.{type_file})'
        )

        if fname:
            dir, name = fname.rsplit('/', 1)
            os.rename(f'rec_im.{type_file}', name)
            try:
                file_from = pathlib.Path(name)
                file_to = pathlib.Path(dir)
                file_from.copy_into(file_to)  # копируем наш файл и путь, делаем копию и переносим в нужный путь
                self.text_result.setText('Сохранено!')
                self.text_result.setStyleSheet('color: violet;')
            except AttributeError as e:
                QMessageBox.warning(
                    self, 'Ошибка сохранения', f'Не удалось сохранить файл: {e}'
                )

    def exit_from_account(self):
        """функция для разлогинивания. Выводится QMessageBox с вопросом хочет ли этого или нет.
        Если не хочет, то ничего не делаем, иначе перезапускаем приложение"""
        reply = QMessageBox.question(
            self,
            "Выход из аккаунта",
            "Вы уверены, что хотите выйти?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.to_register()

    def to_register(self):
        subprocess.Popen([sys.executable] + sys.argv)
        QApplication.quit()

    def sample_in_db(self, title):
        """шаблон для БД"""
        con = sqlite3.connect('users.sqlite')
        cur = con.cursor()
        cur.execute(f"""UPDATE data_users
         SET active = (SELECT type FROM actives WHERE title = ?), 
         time_last_active = ?
         WHERE login = ?""", (title, datetime.datetime.now().isoformat(sep=" ", timespec="seconds"),
                              self.us_login))
        con.commit()
        con.close()

    def log_in_db(self):
        self.sample_in_db('залогинился')

    def encrypt_file(self):
        self.sample_in_db('зашифровал файл')

    def encrypt_text(self):
        self.sample_in_db('зашифровал текст')

    def deciphered_file(self):
        self.sample_in_db('расшифровал файл')

    def deciphered_text(self):
        self.sample_in_db('расшифровал текст')

    def attach_file(self):
        self.sample_in_db('прикрепил файл')

    def save_file(self):
        self.sample_in_db('сохранил картинку')


def cleanup():
    """Пытаемся удалить промежуточные файлы (если они есть)"""
    remove_list = ['created_image.png', 'thumbnail_pic.png']
    if 'type_file' in globals():
        remove_list.append(f'rec_im.{type_file}')

    for item in remove_list:
        try:
            os.remove(item)
        except FileNotFoundError:
            pass

        except PermissionError:  # ничего поделать не могу
            pass

        except OSError as e:
            print(e)
