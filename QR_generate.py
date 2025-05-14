import sys
import os # Добавлен для os.path.abspath и os.path.join
import qrcode
from PIL.ImageQt import ImageQt
from PIL import Image # Убедимся, что Image импортирован для проверки isinstance
import traceback # Для подробной информации об ошибках

from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout,
    QTextEdit, QPushButton, QLabel, QMessageBox,
    QFileDialog, QHBoxLayout
)
from PySide6.QtGui import QPixmap, QIcon
from PySide6.QtCore import Qt, QSize

# --- ОТЛАДОЧНЫЙ ФЛАГ ---
DEBUG = True
# -------------------------

def log_debug(message):
    if DEBUG:
        print(f"[DEBUG] {message}")

def resource_path(relative_path):
    """ Получить абсолютный путь к ресурсу, работает для разработки и для PyInstaller """
    try:
        # PyInstaller создает временную папку и сохраняет путь в _MEIPASS
        base_path = sys._MEIPASS
        log_debug(f"Resource_path: Запуск из PyInstaller, base_path = {base_path}")
    except Exception:
        # sys._MEIPASS не будет определен при запуске из исходного кода Python
        base_path = os.path.abspath(".")
        log_debug(f"Resource_path: Запуск в режиме разработки, base_path = {base_path}")
    return os.path.join(base_path, relative_path)

# Имя файла иконки для окна и панели задач
WINDOW_ICON_FILENAME = "qr.png" # Можно использовать и .ico, если хотите
# Получаем абсолютный путь к иконке окна
WINDOW_ICON_PATH = resource_path(WINDOW_ICON_FILENAME)


class QRCodeGeneratorApp(QWidget):
    def __init__(self):
        super().__init__()
        self.current_qr_image = None
        self.initUI()
        log_debug("Экземпляр QRCodeGeneratorApp инициализирован")

    def initUI(self):
        self.setWindowTitle('Генератор QR-кодов by Python & Qt (DEBUG Mode)' if DEBUG else 'Генератор QR-кодов by Python & Qt')
        
        # Установка иконки окна и панели задач
        try:
            log_debug(f"Попытка установить иконку окна из: {WINDOW_ICON_PATH}")
            if os.path.exists(WINDOW_ICON_PATH):
                self.setWindowIcon(QIcon(WINDOW_ICON_PATH))
                log_debug(f"Иконка окна успешно установлена из: {WINDOW_ICON_PATH}")
            else:
                log_debug(f"ОШИБКА: Файл иконки окна не найден по пути: {WINDOW_ICON_PATH}")
        except Exception as e:
            log_debug(f"ОШИБКА при установке иконки окна из {WINDOW_ICON_PATH}: {e}")
            traceback.print_exc() # Выведем полный traceback ошибки загрузки иконки

        main_layout = QVBoxLayout()
        self.text_input_label = QLabel("Введите текст для QR-кода:")
        main_layout.addWidget(self.text_input_label)
        self.text_input = QTextEdit()
        self.text_input.setPlaceholderText("Например: https://www.example.com")
        self.text_input.setFixedHeight(100)
        main_layout.addWidget(self.text_input)
        self.qr_label = QLabel('Здесь будет QR-код')
        self.qr_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.qr_label.setFixedSize(300, 300)
        self.qr_label.setStyleSheet("border: 1px solid #ccc; background-color: #f0f0f0;")
        main_layout.addWidget(self.qr_label, alignment=Qt.AlignmentFlag.AlignCenter)
        buttons_layout = QHBoxLayout()
        self.generate_button = QPushButton('Сгенерировать QR-код')
        self.generate_button.clicked.connect(self.generate_qr_code)
        self.generate_button.setStyleSheet("padding: 10px; font-size: 14px;")
        buttons_layout.addWidget(self.generate_button)
        self.save_button = QPushButton('Сохранить QR-код')
        self.save_button.clicked.connect(self.save_qr_code)
        self.save_button.setEnabled(False)
        self.save_button.setStyleSheet("padding: 10px; font-size: 14px;")
        buttons_layout.addWidget(self.save_button)
        main_layout.addLayout(buttons_layout)
        self.setLayout(main_layout)
        self.setMinimumSize(400, 550)
        log_debug("UI для QRCodeGeneratorApp создан")

    def generate_qr_code(self):
        log_debug("Начало generate_qr_code()...")
        text_to_encode = self.text_input.toPlainText().strip()
        log_debug(f"Текст для кодирования: '{text_to_encode}' (длина: {len(text_to_encode)})")

        if not text_to_encode:
            log_debug("Текст для кодирования пуст. Показ предупреждения.")
            QMessageBox.warning(self, "Внимание", "Пожалуйста, введите текст для генерации QR-кода.")
            self.qr_label.clear()
            self.qr_label.setText('Здесь будет QR-код')
            self.current_qr_image = None
            self.save_button.setEnabled(False)
            return

        try:
            log_debug("Создание объекта qrcode.QRCode...")
            qr_obj = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            log_debug(f"Параметры QRCode: version={qr_obj.version}, error_correction={qr_obj.error_correction}, box_size={qr_obj.box_size}, border={qr_obj.border}")
            log_debug("Добавление данных в QR-код (qr_obj.add_data)...")
            qr_obj.add_data(text_to_encode)
            log_debug("Данные добавлены.")
            log_debug("Вызов qr_obj.make(fit=True)...")
            qr_obj.make(fit=True)
            log_debug(f"qr_obj.make() выполнен. Актуальная версия QR: {qr_obj.version}")
            log_debug("Создание PIL изображения из QR-кода (qr_obj.make_image)...")
            img_pil_wrapper = qr_obj.make_image(fill_color="black", back_color="white")
            
            if hasattr(img_pil_wrapper, '_img') and isinstance(img_pil_wrapper._img, Image.Image):
                actual_pil_image = img_pil_wrapper._img
            elif isinstance(img_pil_wrapper, Image.Image):
                actual_pil_image = img_pil_wrapper
            else:
                log_debug(f"ОШИБКА: Не удалось извлечь PIL.Image.Image из {type(img_pil_wrapper)}")
                raise TypeError(f"make_image вернул неожиданный тип: {type(img_pil_wrapper)}")

            self.current_qr_image = actual_pil_image
            log_debug(f"qrcode.image.pil.PilImage (wrapper) создан: {type(img_pil_wrapper)}")
            log_debug(f"Извлечен PIL.Image.Image: {type(actual_pil_image)}, размер: {actual_pil_image.size if actual_pil_image else 'None'}")
            log_debug("Конвертация PIL Image в QPixmap (ImageQt, QPixmap.fromImage)...")
            qt_image = ImageQt(actual_pil_image)
            pixmap = QPixmap.fromImage(qt_image)
            log_debug(f"QPixmap создан: isNull={pixmap.isNull()}, размер: {pixmap.size()}")
            log_debug("Масштабирование QPixmap (pixmap.scaled)...")
            scaled_pixmap = pixmap.scaled(
                self.qr_label.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            log_debug(f"QPixmap масштабирован: isNull={scaled_pixmap.isNull()}, размер: {scaled_pixmap.size()}")
            self.qr_label.setPixmap(scaled_pixmap)
            self.save_button.setEnabled(True)
            log_debug("QR-код успешно сгенерирован и отображен.")

        except Exception as e:
            error_type = type(e).__name__
            error_msg = str(e)
            log_debug(f"ОШИБКА при генерации QR: Тип={error_type}, Сообщение='{error_msg}'")
            if DEBUG:
                print("\n--- Трассировка ошибки генерации QR ---")
                traceback.print_exc()
                print("-------------------------------------\n")
                detailed_error_msg = f"Не удалось сгенерировать QR-код.\n\nТип ошибки: {error_type}\nСообщение: {error_msg}\n\nПодробности в консоли."
            else:
                detailed_error_msg = f"Не удалось сгенерировать QR-код: {error_msg}"
            QMessageBox.critical(self, "Ошибка генерации", detailed_error_msg)
            self.qr_label.clear()
            self.qr_label.setText('Ошибка генерации')
            self.current_qr_image = None
            self.save_button.setEnabled(False)

    def save_qr_code(self):
        log_debug("Начало save_qr_code()...")
        if not self.current_qr_image:
            log_debug("Попытка сохранить пустой QR-код. Показ предупреждения.")
            QMessageBox.warning(self, "Внимание", "Сначала сгенерируйте QR-код, чтобы его сохранить.")
            return
        options = QFileDialog.Options()
        filePath, _ = QFileDialog.getSaveFileName(
            self, "Сохранить QR-код", "qr_code.png",
            "PNG Files (*.png);;JPEG Files (*.jpg *.jpeg);;All Files (*)",
            options=options
        )
        if filePath:
            log_debug(f"Файл для сохранения выбран: {filePath}")
            try:
                self.current_qr_image.save(filePath)
                QMessageBox.information(self, "Успех", f"QR-код успешно сохранен в:\n{filePath}")
                log_debug("QR-код успешно сохранен.")
            except Exception as e:
                error_type = type(e).__name__; error_msg = str(e)
                log_debug(f"ОШИБКА при сохранении: Тип={error_type}, Сообщение='{error_msg}'")
                if DEBUG: print("\n--- Трассировка ошибки сохранения ---"); traceback.print_exc(); print("-----------------------------------\n")
                QMessageBox.critical(self, "Ошибка сохранения", f"Не удалось сохранить файл: {e}")
        else:
            log_debug("Сохранение отменено пользователем.")

# --- КОНЕЦ КЛАССА QRCodeGeneratorApp ---

def main():
    log_debug("Вызов main()")
    app = QApplication(sys.argv)
    log_debug("QApplication создан.")

    if DEBUG:
        log_debug("--- Информация о системе и библиотеках ---")
        log_debug(f"Python: {sys.version.splitlines()[0]}")
        try: import PySide6 as PySide6Module; log_debug(f"PySide6: {PySide6Module.__version__}")
        except ImportError: log_debug("PySide6: модуль не найден (ImportError)")
        except AttributeError: log_debug("PySide6: версию не удалось определить (атрибут __version__ отсутствует)")
        except Exception as e: log_debug(f"PySide6: не удалось определить версию (ошибка: {e})")
        try: log_debug(f"qrcode version (attempt): {qrcode.__version__}")
        except AttributeError:
            log_debug("qrcode: ВЕРСИЮ НЕ УДАЛОСЬ ОПРЕДЕЛИТЬ (атрибут __version__ отсутствует).")
            try: log_debug(f"qrcode module path: {qrcode.__file__}")
            except AttributeError: log_debug("qrcode module path: не удалось определить (нет атрибута __file__).")
        except Exception as e: log_debug(f"qrcode: не удалось определить версию (непредвиденная ошибка: {e})")
        try:
            log_debug(f"Pillow: {Image.__version__}")
            log_debug(f"Pillow (PIL) Image module path: {Image.__file__}")
        except AttributeError:
            try: from PIL import __version__ as PIL_VERSION_DIRECT; log_debug(f"Pillow (direct import): {PIL_VERSION_DIRECT}")
            except Exception: log_debug("Pillow: версию не удалось определить.")
        except Exception as e: log_debug(f"Pillow: не удалось определить версию/путь (ошибка: {e})")
        log_debug("--- Конец информации о системе и библиотеках ---")
    
    log_debug("Создание экземпляра QRCodeGeneratorApp...")
    window = QRCodeGeneratorApp()
    log_debug("Экземпляр QRCodeGeneratorApp создан в main.")
    log_debug("Вызов window.show()...")
    window.show()
    log_debug("window.show() вызван.")
    log_debug("Вызов app.exec()... Приложение входит в цикл событий.")
    exit_code = app.exec()
    log_debug(f"app.exec() завершен. Код выхода: {exit_code}")
    sys.exit(exit_code)

if __name__ == '__main__':
    log_debug(f"Скрипт запущен как главный (__name__ is '{__name__}')")
    main()
    log_debug("Выполнение после main() завершено (если sys.exit не прервал).")
