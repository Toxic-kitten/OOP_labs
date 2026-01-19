import json
from enum import Enum
from typing import Dict, List, Optional, ClassVar
import time


class Color(Enum):
    """Перечисление цветов для текста"""
    BLACK = 30
    RED = 31
    GREEN = 32
    YELLOW = 33
    BLUE = 34
    MAGENTA = 35
    CYAN = 36
    WHITE = 37
    BRIGHT_BLACK = 90
    BRIGHT_RED = 91
    BRIGHT_GREEN = 92
    BRIGHT_YELLOW = 93
    BRIGHT_BLUE = 94
    BRIGHT_MAGENTA = 95
    BRIGHT_CYAN = 96
    BRIGHT_WHITE = 97


class ANSI:
    """ANSI escape codes только для цветов"""
    RESET = '\033[0m'

    @staticmethod
    def set_color(color: Color) -> str:
        return f'\033[{color.value}m'


class FontLoader:
    """Загрузчик шрифтов из файлов"""
    @staticmethod
    def load_font(filename: str) -> Dict[str, List[str]]:
        """Загружает шрифт из файла"""
        """Обработка ошибок"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Font file {filename} not found!")
        except PermissionError:
            print(f"Ошибка: нет прав доступа к файлу '{filename}'")
        except IsADirectoryError:
            print(f"Ошибка: '{filename}' является директорией, а не файлом")
        except UnicodeDecodeError as e:
            print(f"Ошибка: проблема с кодировкой файла '{filename}'")
            print(f"Проблема в кодировке {e.encoding}")
        except json.JSONDecodeError as e:
            print(f"Ошибка JSON в файле {filename}: в строке {e.lineno}, столбце {e.colno}")
        except OSError as e:
            print(f"Системная ошибка: {e} в файле {filename}")


class Printer:
    """Класс для красивого вывода текста в консоль"""

    _current_font: ClassVar[Optional[Dict[str, List[str]]]] = None
    _font_height: ClassVar[int] = 0

    def __init__(self, color: Color = Color.WHITE, symbol: str = '*', font_file: str = None):
        self.color = color
        self.symbol = symbol

        if font_file:
            self.load_font(font_file)

    def __enter__(self):
        """Вход в контекстный manager"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Выход из контекстного менеджера"""
        print(ANSI.RESET, end='')

    @classmethod
    def load_font(cls, font_file: str):
        """Загружает шрифт для класса"""
        cls._current_font = FontLoader.load_font(font_file)
        if cls._current_font:
            first_char = next(iter(cls._current_font.values()))
            cls._font_height = len(first_char)

    @classmethod
    def _is_wide_symbol(cls, symbol: str) -> bool:
        """Проверяет, является ли символ широким"""
        wide_symbols = {'★', '◘', '♦', '♠', '♥', '◆', '♣', '△', '▽'}
        return symbol in wide_symbols

    @classmethod
    def print(cls, text: str, color: Color = Color.WHITE, symbol: str = '*'):
        """Статический метод для вывода текста"""
        if cls._is_wide_symbol(symbol):
            print(f"Ошибка: символ '{symbol}' недопустим. Используйте только однобайтовые символы.")
            return  # Выходим из метода

        lines = [''] * cls._font_height

        for char in text.upper():
            if char == ' ':
                # Добавляем пробелы во все строки
                for i in range(cls._font_height):
                    lines[i] += ' ' * 5
                continue

            if char in cls._current_font:
                char_pattern = cls._current_font[char]

                for i, line in enumerate(char_pattern):
                    rendered_line = line.replace('*', symbol)
                    # Дополняем пробелами справа до fixed_width
                    padded_line = rendered_line.center(cls._font_height)
                    lines[i] += padded_line + ' '  # пробел между символами

        # Выводим все строки
        for line in lines:
            print(ANSI.set_color(color) + line + ANSI.RESET)

    def print_text(self, text: str):
        """Вывод текста с настройками экземпляра"""
        self.__class__.print(text, self.color, self.symbol)
        print()  # Добавляем пустую строку между текстами


def demonstrate_printer() -> None:
    """Демонстрация работы класса Printer"""

    print("=== ДЕМОНСТРАЦИЯ РАБОТЫ КЛАССА PRINTER ===\n")

    # Демонстрация 1: Статическое использование со шрифтом высотой 5
    print("1. Статическое использование (шрифт 5x5):")
    Printer.load_font('font5x5.json')
    Printer.print("HELLO", Color.RED, '#')
    print()
    Printer.print("WORLD", Color.GREEN, '@')

    time.sleep(2)
    print("\n" + "=" * 50 + "\n")

    # Демонстрация 2: Использование с контекстным менеджером
    print("2. Использование с контекстным менеджером (шрифт 5x5):")

    with Printer(Color.MAGENTA, '$', 'font5x5.json') as printer:
        printer.print_text("CONTEXT")
        printer.print_text("MANAGER")

    time.sleep(2)
    print("\n" + "=" * 50 + "\n")

    # Демонстрация 3: Смена шрифта на высоту 7
    print("3. Смена шрифта на 7x7:")
    Printer.load_font('font7x7.json')

    Printer.print("BIG", Color.BRIGHT_YELLOW, '■')
    print()
    Printer.print("FONT", Color.BRIGHT_CYAN, '●')

    time.sleep(2)
    print("\n" + "=" * 50 + "\n")

    # Демонстрация 4: Разные цвета и символы
    print("4. Разные цвета и символы (шрифт 7x7):")

    Printer.load_font('font7x7.json')
    Printer.print("COLOR", Color.BRIGHT_RED, '□')
    print()
    Printer.print("FIRST", Color.BRIGHT_GREEN, '○')
    print()
    Printer.print("DEMO", Color.BRIGHT_BLUE, '@')

    time.sleep(2)
    print("\n" + "=" * 50 + "\n")

    # Демонстрация 5: Смешанное использование
    print("5. Смешанное использование:")

    # Статический вызов
    Printer.load_font('font7x7.json')
    Printer.print("STATIC", Color.BRIGHT_MAGENTA, '▲')
    print()

    # Контекстный менеджер
    with Printer(Color.BRIGHT_YELLOW, '6', 'font7x7.json') as p:
        p.print_text("YELLOW")

    print("\n" + "=" * 50)
    print("Демонстрация завершена!")


if __name__ == "__main__":
    demonstrate_printer()