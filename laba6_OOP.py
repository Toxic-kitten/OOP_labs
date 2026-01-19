import json
from typing import Protocol, Dict, Any, List, Optional
from abc import ABC, abstractmethod
import os
import sys


class Command(Protocol):
    """Протокол для команд"""

    @abstractmethod
    def execute(self) -> str:
        """Выполнить команду"""
        pass

    @abstractmethod
    def undo(self) -> str:
        """Отменить команду"""
        pass

    @abstractmethod
    def redo(self) -> str:
        """Повторить команду"""
        pass

    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """Каждая команда должна уметь превращать себя в словарь"""
        pass

    @classmethod
    @abstractmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Command':
        """Каждая команда должна уметь создавать себя из словаря"""
        pass


############################################################
# КЛАССЫ КОМАНД (не зависят от Keyboard)
############################################################

class KeyCommand(Command):
    """Команда для печати символа"""

    def __init__(self, symbol: str):
        self.symbol = symbol

    def execute(self) -> str:
        """Вернуть символ для печати"""
        return self.symbol

    def undo(self) -> str:
        """Команда для удаления символа"""
        return "[BACKSPACE]"

    def redo(self) -> str:
        """Повторить печать символа"""
        return self.symbol

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "KeyCommand",  # Указываем свой тип
            "symbol": self.symbol
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'KeyCommand':
        return cls(symbol=data["symbol"])


class VolumeUpCommand(Command):
    """Команда для увеличения громкости"""

    def __init__(self, step: int = 10):
        self.step = step

    def execute(self) -> str:
        return f"volume increased +{self.step}%"

    def undo(self) -> str:
        return f"volume decreased +{self.step}%"

    def redo(self) -> str:
        return self.execute()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "VolumeUpCommand",
            "step": self.step
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'VolumeUpCommand':
        return cls(step=data.get("step", 10))


class VolumeDownCommand(Command):
    """Команда для уменьшения громкости"""

    def __init__(self, step: int = 10):
        self.step = step

    def execute(self) -> str:
        return f"volume decreased +{self.step}%"

    def undo(self) -> str:
        return f"volume increased +{self.step}%"

    def redo(self) -> str:
        return self.execute()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "VolumeDownCommand",
            "step": self.step
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'VolumeDownCommand':
        return cls(step=data.get("step", 10))


class MediaPlayerCommand(Command):
    def execute(self) -> str:
        return "media player launched"

    def undo(self) -> str:
        return "media player closed"

    def redo(self) -> str:
        return self.execute()

    def to_dict(self) -> Dict[str, Any]:
        return {"type": "MediaPlayerCommand"}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MediaPlayerCommand':
        return cls()


############################################################
# КЛАСС ДЛЯ ПРЕДСТАВЛЕНИЯ ОБЪЕКТА В ВИДЕ СЛОВАРЯ
############################################################

class CommandDictRepresentation:
    """Класс для представления команд в виде словаря"""
    # изменить
    @staticmethod
    def to_dict(command: Command) -> Dict[str, Any]:
        """Преобразовать команду в словарь"""
        if isinstance(command, KeyCommand):
            return {
                "type": "KeyCommand",
                "symbol": command.symbol
            }
        elif isinstance(command, VolumeUpCommand):
            return {
                "type": "VolumeUpCommand",
                "step": command.step
            }
        elif isinstance(command, VolumeDownCommand):
            return {
                "type": "VolumeDownCommand",
                "step": command.step
            }
        elif isinstance(command, MediaPlayerCommand):
            return {
                "type": "MediaPlayerCommand"
            }
        else:
            raise ValueError(f"Unknown command type: {type(command)}")

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> Command:
        """Создать команду из словаря"""
        cmd_type = data.get("type")

        if cmd_type == "KeyCommand":
            return KeyCommand(data["symbol"])
        elif cmd_type == "VolumeUpCommand":
            return VolumeUpCommand(data["step"])
        elif cmd_type == "VolumeDownCommand":
            return VolumeDownCommand(data["step"])
        elif cmd_type == "MediaPlayerCommand":
            return MediaPlayerCommand()
        else:
            raise ValueError(f"Unknown command type: {cmd_type}")


############################################################
# КЛАСС ДЛЯ СЕРИАЛИЗАЦИИ И ДЕСЕРИАЛИЗАЦИИ
############################################################

class KeyboardSerializer:
    """Класс для сериализации и десериализации состояния клавиатуры"""

    def __init__(self, filename: str):
        self.filename = filename

    def serialize(self, key_binds: Dict[str, Command]) -> None:
        """Сериализовать привязки клавиш в файл"""
        try:
            # Преобразуем команды в словари
            serialized_data = {}
            for key, command in key_binds.items():
                serialized_data[key] = CommandDictRepresentation.to_dict(command) # Тут изменить

            # Сохраняем в файл
            with open(self.filename, 'w', encoding='utf-8') as f:
                json.dump(serialized_data, f, indent=2, ensure_ascii=False)

            print(f"✓ Состояние клавиатуры сохранено в {self.filename}")
        except Exception as e:
            print(f"✗ Ошибка при сохранении: {e}")

    def deserialize(self) -> Dict[str, Command]:
        """Десериализовать привязки клавиш из файла"""
        try:
            if not os.path.exists(self.filename):
                print(f"Файл {self.filename} не найден, будут созданы настройки по умолчанию")
                return {}

            with open(self.filename, 'r', encoding='utf-8') as f:
                serialized_data = json.load(f)

            # Преобразуем словари обратно в команды
            key_binds = {}
            for key, command_dict in serialized_data.items():
                key_binds[key] = CommandDictRepresentation.from_dict(command_dict)

            print(f"✓ Состояние клавиатуры загружено из {self.filename}")
            return key_binds
        except Exception as e:
            print(f"✗ Ошибка при загрузке: {e}")
            return {}


############################################################
# КЛАСС ВИРТУАЛЬНОЙ КЛАВИАТУРЫ
############################################################
class State(ABC):
    """Абстрактный класс состояния"""

    @abstractmethod
    def update(self, command_result: str) -> None:
        pass

    @abstractmethod
    def get_state(self) -> Dict[str, Any]:
        pass


class TextState(State):
    """Состояние текста"""

    def __init__(self):
        self._current_text: str = ""

    def update(self, command_result: str) -> None:
        if command_result == "[BACKSPACE]":
            if self._current_text:
                self._current_text = self._current_text[:-1]
        elif len(command_result) == 1 and command_result not in ["[", "]"]:
            self._current_text += command_result

    def get_state(self) -> Dict[str, Any]:
        return {"text": self._current_text}

    @property
    def text(self) -> str:
        return self._current_text


class VolumeState(State):
    """Состояние громкости"""

    def __init__(self, initial_volume: int = 50):
        self._volume: int = initial_volume

    def update(self, command_result: str) -> None:
        if "volume increased" in command_result:
            step = int(command_result.split('+')[1].replace('%', ''))
            self._volume = min(100, self._volume + step)
        elif "volume decreased" in command_result:
            step = int(command_result.split('+')[1].replace('%', ''))
            self._volume = max(0, self._volume - step)

    def get_state(self) -> Dict[str, Any]:
        return {"volume": self._volume}

    @property
    def volume(self) -> int:
        return self._volume


class MediaState(State):
    """Состояние медиаплеера"""

    def __init__(self):
        self._is_playing: bool = False

    def update(self, command_result: str) -> None:
        if result == "media player launched":
            self._is_playing = True
        elif result == "media player closed":
            self._is_playing = False

    def get_state(self) -> Dict[str, Any]:
        return {"media_playing": self._is_playing}

    @property
    def is_playing(self) -> bool:
        return self._is_playing


class History:
    """Класс для управления историей команд"""

    def __init__(self):
        self._command_history: List[Command] = []
        self._history_pointer: int = -1

    def add(self, command: Command) -> None:
        """Добавить команду в историю"""
        # Если мы находимся не в конце истории, удаляем все после указателя
        if self._history_pointer < len(self._command_history) - 1:
            self._command_history = self._command_history[:self._history_pointer + 1]

        self._command_history.append(command)
        self._history_pointer += 1

    def undo(self) -> Optional[Command]:
        """Вернуть команду для отмены"""
        if self._history_pointer >= 0:
            command = self._command_history[self._history_pointer]
            self._history_pointer -= 1
            return command
        return None

    def redo(self) -> Optional[Command]:
        """Вернуть команду для повтора"""
        if self._history_pointer < len(self._command_history) - 1:
            self._history_pointer += 1
            return self._command_history[self._history_pointer]
        return None

    def get_state(self) -> Dict[str, Any]:
        """Получить состояние истории"""
        return {
            "history_size": len(self._command_history),
            "history_pointer": self._history_pointer
        }


class Keyboard:
    """Виртуальная клавиатура с поддержкой undo/redo"""

    def __init__(self):
        self._key_binds: Dict[str, Command] = {}
        self._history = History()
        self._states: Dict[str, State] = {
            "text": TextState(),
            "volume": VolumeState(),
            "media": MediaState()
        }
        self._output_log: List[str] = []

    @property
    def key_binds(self) -> Dict[str, Command]:
        """Получить текущие привязки клавиш"""
        return self._key_binds.copy()

    @key_binds.setter
    def key_binds(self, binds: Dict[str, Command]) -> None:
        """Установить привязки клавиш"""
        self._key_binds = binds

    def bind_key(self, key: str, command: Command) -> None:
        """Добавить или изменить привязку клавиши"""
        self._key_binds[key] = command

    def unbind_key(self, key: str) -> None:
        """Удалить привязку клавиши"""
        if key in self._key_binds:
            del self._key_binds[key]

    def execute_command(self, key: str) -> None:
        """Выполнить команду, связанную с клавишей"""
        if key not in self._key_binds:
            print(f"✗ Клавиша '{key}' не назначена")
            return

        command = self._key_binds[key]

        # Выполняем команду
        result = command.execute()

        # Обрабатываем результат во всех состояниях
        self._process_command_result(result)

        # Добавляем в историю
        self._history.add(command)

        # Записываем в лог
        self._output_log.append(result)

    def undo(self) -> None:
        """Отменить последнюю команду"""
        command = self._history.undo()
        if command:
            result = command.undo()
            self._process_command_result(result)
            self._output_log.append("undo")
        else:
            print("✗ Нечего отменять")

    def redo(self) -> None:
        """Повторить отмененную команду"""
        command = self._history.redo()
        if command:
            result = command.redo()
            self._process_command_result(result)
            self._output_log.append("redo")
        else:
            print("✗ Нечего повторять")

    def _process_command_result(self, result: str) -> None:
        """Обработать результат выполнения команды"""
        # Обновляем все состояния
        for state in self._states.values():
            state.update(result)

    def get_current_state(self) -> Dict[str, Any]:
        """Получить текущее состояние клавиатуры"""
        state = {}
        for name, state_obj in self._states.items():
            state.update(state_obj.get_state())
        state.update(self._history.get_state())
        return state

    def get_output_log(self) -> List[str]:
        """Получить лог вывода"""
        return self._output_log.copy()

    # Геттеры для конкретных состояний
    @property
    def text(self) -> str:
        return self._states["text"].text

    @property
    def volume(self) -> int:
        return self._states["volume"].volume

    @property
    def is_media_playing(self) -> bool:
        return self._states["media"].is_playing
# class Keyboard:
#     """Виртуальная клавиатура с поддержкой undo/redo"""
#     # Убрать лишние поля и сделать так, чтобы класс клавиатуры не работал с лишними данными
#     def __init__(self):
#         self._key_binds: Dict[str, Command] = {}
#         self._command_history: List[Command] = []
#         self._history_pointer: int = -1
#         self._current_text: str = ""
#         self._volume: int = 50
#         self._is_media_playing: bool = False
#         self._output_log: List[str] = []
#
#     @property
#     def key_binds(self) -> Dict[str, Command]:
#         """Получить текущие привязки клавиш"""
#         return self._key_binds.copy()
#
#     @key_binds.setter
#     def key_binds(self, binds: Dict[str, Command]) -> None:
#         """Установить привязки клавиш"""
#         self._key_binds = binds
#
#     def bind_key(self, key: str, command: Command) -> None:
#         """Добавить или изменить привязку клавиши"""
#         self._key_binds[key] = command
#
#     def unbind_key(self, key: str) -> None:
#         """Удалить привязку клавиши"""
#         if key in self._key_binds:
#             del self._key_binds[key]
#
#     def execute_command(self, key: str) -> None:
#         """Выполнить команду, связанную с клавишей"""
#         if key not in self._key_binds:
#             print(f"✗ Клавиша '{key}' не назначена")
#             return
#
#         command = self._key_binds[key]
#
#         # Если мы находимся не в конце истории, удаляем все после указателя
#         if self._history_pointer < len(self._command_history) - 1:
#             self._command_history = self._command_history[:self._history_pointer + 1]
#
#         # Выполняем команду и добавляем в историю
#         result = command.execute()
#         self._process_command_result(result)
#         self._command_history.append(command)
#         self._history_pointer += 1
#
#         # Записываем в лог
#         self._output_log.append(result)
#
#     def undo(self) -> None:
#         """Отменить последнюю команду"""
#         if self._history_pointer >= 0:
#             command = self._command_history[self._history_pointer]
#             result = command.undo()
#             self._process_command_result(result)
#             self._history_pointer -= 1
#             self._output_log.append("undo")
#         else:
#             print("✗ Нечего отменять")
#
#     def redo(self) -> None:
#         """Повторить отмененную команду"""
#         if self._history_pointer < len(self._command_history) - 1:
#             self._history_pointer += 1
#             command = self._command_history[self._history_pointer]
#             result = command.redo()
#             self._process_command_result(result)
#             self._output_log.append("redo")
#         else:
#             print("✗ Нечего повторять")
#
#     # изменить
#     def _process_command_result(self, result: str) -> None:
#         """Обработать результат выполнения команды"""
#         if result == "[BACKSPACE]":
#             if self._current_text:
#                 self._current_text = self._current_text[:-1]
#         elif "volume increased" in result:
#             step = int(result.split('+')[1].replace('%', ''))
#             self._volume = min(100, self._volume + step)
#         elif "volume decreased" in result:
#             step = int(result.split('+')[1].replace('%', ''))
#             self._volume = max(0, self._volume - step)
#         elif result == "media player launched":
#             self._is_media_playing = True
#         elif result == "media player closed":
#             self._is_media_playing = False
#         elif len(result) == 1 and result not in ["[", "]"]:  # Обычный символ
#             self._current_text += result
#
#     def get_current_state(self) -> Dict[str, Any]:
#         """Получить текущее состояние клавиатуры"""
#         return {
#             "text": self._current_text,
#             "volume": self._volume,
#             "media_playing": self._is_media_playing,
#             "history_size": len(self._command_history),
#             "history_pointer": self._history_pointer
#         }
#
#     def get_output_log(self) -> List[str]:
#         """Получить лог вывода"""
#         return self._output_log.copy()


############################################################
# КЛАСС ДЛЯ СОХРАНЕНИЯ И ВОССТАНОВЛЕНИЯ СОСТОЯНИЯ (MEMENTO)
############################################################

class KeyboardStateSaver:
    """Класс для сохранения и восстановления состояния клавиатуры (Memento)"""

    def __init__(self, serializer: KeyboardSerializer):
        self.serializer = serializer

    def save_state(self, keyboard: Keyboard) -> None:
        """Сохранить состояние клавиатуры"""
        self.serializer.serialize(keyboard.key_binds)

    def load_state(self) -> Dict[str, Command]:
        """Загрузить состояние клавиатуры"""
        return self.serializer.deserialize()


############################################################
# ДЕМОНСТРАЦИЯ РАБОТЫ ПРОГРАММЫ
############################################################

def check_and_create_output_files():
    """Проверить существование файлов и создать их если нужно"""

    # Папка для вывода
    output_dir = "lab6_output"

    # Проверяем, существует ли папка
    if not os.path.exists(output_dir):
        print("=" * 60)
        print("ВНИМАНИЕ: Папка 'lab6_output' не найдена!")
        print("=" * 60)
        print("Пожалуйста, создайте папку вручную:")
        print(f"1. Создайте папку с именем '{output_dir}'")
        print(f"2. Рядом с файлом программы")
        print("=" * 60)
        return False, None, None, None

    # Пути к файлам
    console_output_file = os.path.join(output_dir, "console_output.txt")
    journal_file = os.path.join(output_dir, "journal.txt")
    state_file = os.path.join(output_dir, "keyboard_state.json")

    return True, console_output_file, journal_file, state_file


def main():
    """Основная функция демонстрации"""

    # Проверяем и получаем пути к файлам
    success, console_output_file, journal_file, state_file = check_and_create_output_files()

    if not success:
        print("Программа завершена. Создайте папку 'lab6_output' и запустите снова.")
        return

    print(f"✓ Файлы будут сохранены в папку: lab6_output/")
    print(f"  1. {os.path.basename(console_output_file)} - вывод программы")
    print(f"  2. {os.path.basename(journal_file)} - журнал команд")
    print(f"  3. {os.path.basename(state_file)} - состояние клавиатуры")
    print()

    # Сохраняем вывод в файл и в консоль
    class Tee:
        """Класс для вывода одновременно в консоль и в файл"""

        def __init__(self, *files):
            self.files = files

        def write(self, obj):
            for f in self.files:
                f.write(obj)

        def flush(self):
            for f in self.files:
                f.flush()

    # Открываем файл для вывода
    with open(console_output_file, 'w', encoding='utf-8') as f:
        original_stdout = sys.stdout
        sys.stdout = Tee(original_stdout, f)

        try:
            print("=" * 60)
            print("ЛАБОРАТОРНАЯ РАБОТА 6: ВИРТУАЛЬНАЯ КЛАВИАТУРА")
            print("=" * 60)

            # 1. Создаем клавиатуру
            keyboard = Keyboard()

            # 2. Создаем сериализатор и сохранитель состояния
            serializer = KeyboardSerializer(state_file)
            state_saver = KeyboardStateSaver(serializer)

            # 3. Загружаем сохраненное состояние (или создаем по умолчанию)
            saved_binds = state_saver.load_state()

            if not saved_binds:
                print("\nСоздание привязок по умолчанию:")
                # Создаем привязки по умолчанию
                saved_binds = {
                    "a": KeyCommand("a"),
                    "b": KeyCommand("b"),
                    "c": KeyCommand("c"),
                    "d": KeyCommand("d"),
                    "ctrl++": VolumeUpCommand(20),
                    "ctrl+-": VolumeDownCommand(20),
                    "ctrl+p": MediaPlayerCommand(),
                    "space": KeyCommand(" "),
                    "enter": KeyCommand("\n"),
                }
                print("✓ Привязки по умолчанию созданы")

            keyboard.key_binds = saved_binds

            # 4. Сохраняем состояние (создает файл если его нет)
            state_saver.save_state(keyboard)

            print("\n" + "=" * 60)
            print("ТЕСТИРОВАНИЕ КОМАНД")
            print("=" * 60)

            # 5. Тестируем команды
            test_sequence = [
                "a", "b", "c",  # Печать символов
                "undo", "undo",  # Отмена
                "redo",  # Повтор
                "ctrl++",  # Увеличение громкости
                "ctrl+-",  # Уменьшение громкости
                "ctrl+p",  # Запуск медиаплеера
                "d",  # Печать символа
                "undo", "undo"  # Двойная отмена
            ]

            print("\nВыполняемая последовательность команд:")
            print(" -> ".join(test_sequence))

            print("\nРезультат выполнения:")
            for key in test_sequence:
                if key == "undo":
                    keyboard.undo()
                elif key == "redo":
                    keyboard.redo()
                elif key in keyboard.key_binds:
                    keyboard.execute_command(key)
                else:
                    print(f"✗ Неизвестная команда: {key}")

            # 6. Выводим текущее состояние
            print("\n" + "=" * 60)
            print("ТЕКУЩЕЕ СОСТОЯНИЕ КЛАВИАТУРЫ")
            print("=" * 60)

            state = keyboard.get_current_state()
            print(f"Текст: '{state['text']}'")
            print(f"Громкость: {state['volume']}%")
            print(f"Медиаплеер: {'запущен' if state['media_playing'] else 'остановлен'}")
            print(f"Размер истории: {state['history_size']}")
            print(f"Указатель истории: {state['history_pointer']}")

            # 7. Сохраняем журнал в файл
            print("\n" + "=" * 60)
            print("СОХРАНЕНИЕ ЖУРНАЛА В ФАЙЛ")
            print("=" * 60)

            with open(journal_file, 'w', encoding='utf-8') as journal:
                output_log = keyboard.get_output_log()
                current_text = ""

                for entry in output_log:
                    journal.write(entry + "\n")

                    # Формируем текст для демонстрации
                    if entry == "[BACKSPACE]":
                        if current_text:
                            current_text = current_text[:-1]
                    elif entry in ["undo", "redo"]:
                        pass  # undo/redo уже записаны в лог
                    elif len(entry) == 1 and entry not in ["[", "]"]:
                        current_text += entry

                    # Выводим текущее состояние текста после каждой операции
                    # if entry not in ["undo", "redo"]:
                    #     print(f"{entry:25} | Текст: '{current_text}'")
                    # else:
                    #     print(f"{entry:25} |")
                    print(f"{entry:25} | Текст: '{current_text}'")

            print(f"\n✓ Журнал сохранен в файл: {journal_file}")
            print(f"✓ Вывод консоли сохранен в файл: {console_output_file}")
            print(f"✓ Состояние клавиатуры сохранено в файл: {state_file}")

            print("\n" + "=" * 60)
            print("ПРОВЕРКА UNDO/REDO С ИСТОРИЕЙ")
            print("=" * 60)

            # Дополнительная проверка undo/redo
            print("\nДополнительный тест истории:")
            print("Выполняем команды: d -> e -> undo -> undo -> redo -> redo")

            # Добавляем новые привязки
            keyboard.bind_key("e", KeyCommand("e"))

            test_sequence2 = ["d", "e", "undo", "undo", "redo", "redo"]
            for key in test_sequence2:
                if key == "undo":
                    keyboard.undo()
                elif key == "redo":
                    keyboard.redo()
                else:
                    keyboard.execute_command(key)

            final_state = keyboard.get_current_state()
            print(f"Финальный текст: '{final_state['text']}'")

            # 8. Сохраняем финальное состояние
            state_saver.save_state(keyboard)
            print(f"✓ Финальное состояние сохранено в {state_file}")

        finally:
            # Восстанавливаем стандартный вывод
            sys.stdout = original_stdout

    print("\n" + "=" * 60)
    print("ПРОГРАММА УСПЕШНО ВЫПОЛНЕНА!")
    print("=" * 60)
    print(f"✓ Файлы успешно сохранены в папке: lab6_output/")
    print("Откройте файлы для просмотра результатов:")
    print(f"1. {console_output_file} - полный вывод программы")
    print(f"2. {journal_file} - журнал выполненных команд")
    print(f"3. {state_file} - состояние клавиатуры (JSON)")
    print("\nДля повторного запуска - просто запустите программу снова!")


if __name__ == "__main__":
    main()
