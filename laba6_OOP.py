import json
import os
import sys
from typing import Type
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional

# =============================
# 1. БАЗОВЫЙ ИНТЕРФЕЙС КОМАНДЫ
# =============================


class Command(ABC):
    """Абстрактный базовый класс для всех команд"""

    @abstractmethod
    def execute(self) -> str:
        pass

    @abstractmethod
    def undo(self) -> str:
        pass

    @abstractmethod
    def redo(self) -> str:
        pass

    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        pass

    @classmethod
    @abstractmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Command':
        pass


# =============================
# 2. RECEIVER: TEXT BUFFER
# =============================

class TextBuffer:
    """Получатель (receiver) для текстовых операций — хранит состояние текста"""

    def __init__(self):
        self._text = ""

    def insert_char(self, char: str):
        self._text += char

    def delete_last_char(self):
        if self._text:
            self._text = self._text[:-1]

    def get_text(self) -> str:
        return self._text

    def clear(self):
        self._text = ""


# =============================
# 3. КОНКРЕТНЫЕ КОМАНДЫ
# =============================

class KeyCommand(Command):
    """Команда для печати символа"""
    command_type = "KeyCommand"

    def __init__(self, symbol: str, buffer: Optional[TextBuffer] = None):
        self.symbol = symbol
        self.buffer = buffer

    def set_buffer(self, buffer: TextBuffer):
        """Установить буфер после создания команды"""
        self.buffer = buffer

    def execute(self) -> str:
        if self.buffer:
            self.buffer.insert_char(self.symbol)
        return self.symbol

    def undo(self) -> str:
        if self.buffer:
            self.buffer.delete_last_char()
        return "[BACKSPACE]"

    def redo(self) -> str:
        return self.execute()

    def to_dict(self) -> Dict[str, Any]:
        return {"type": "KeyCommand", "symbol": self.symbol}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'KeyCommand':
        # buffer будет установлен позже через set_buffer()
        return cls(data["symbol"])

    # @staticmethod
    # @register_command("KeyCommand")
    # def from_dict_and_buffer(data: Dict[str, Any], buffer: Optional[TextBuffer]) -> 'KeyCommand':
    #     return KeyCommand(data["symbol"], buffer)


class VolumeUpCommand(Command):
    """Команда увеличения громкости"""
    command_type = "VolumeUpCommand"

    def __init__(self, step: int = 10):
        self.step = step

    def execute(self) -> str:
        return f"volume increased +{self.step}%"

    def undo(self) -> str:
        return f"volume decreased -{self.step}%"

    def redo(self) -> str:
        return self.execute()

    def to_dict(self) -> Dict[str, Any]:
        return {"type": "VolumeUpCommand", "step": self.step}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'VolumeUpCommand':
        return cls(step=data.get("step", 10))


class VolumeDownCommand(Command):
    """Команда уменьшения громкости"""
    command_type = "VolumeDownCommand"

    def __init__(self, step: int = 10):
        self.step = step

    def execute(self) -> str:
        return f"volume decreased -{self.step}%"

    def undo(self) -> str:
        return f"volume increased +{self.step}%"

    def redo(self) -> str:
        return self.execute()

    def to_dict(self) -> Dict[str, Any]:
        return {"type": "VolumeDownCommand", "step": self.step}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'VolumeDownCommand':
        return cls(step=data.get("step", 10))


class MediaPlayerCommand(Command):
    """Команда запуска медиаплеера (одноразовая: launch → undo = close)"""
    command_type = "MediaPlayerCommand"

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


# =============================
# 4. КЛАСС КЛАВИАТУРЫ
# =============================

class Keyboard:
    def __init__(self, text_buffer: TextBuffer):
        self._key_binds: Dict[str, Command] = {}
        self._history: List[Command] = []
        self._history_ptr = -1
        self._text_buffer = text_buffer

    # публичный метод для безопасного изменения привязки клавиш
    def bind_key(self, key: str, command: Command):
        self._key_binds[key] = command

    def get_key_binds_dict_for_save(self) -> Dict[str, Dict[str, Any]]:
        """Возвращает словарь для сохранения (без объектов Command)"""
        return {k: cmd.to_dict() for k, cmd in self._key_binds.items()}

    def execute(self, key: str) -> str:
        if key not in self._key_binds:
            return f"unknown key: {key}"

        # Если мы находимся не в конце истории, обрезаем ее
        if self._history_ptr < len(self._history) - 1:
            self._history = self._history[:self._history_ptr + 1]

        cmd = self._key_binds[key]
        result = cmd.execute()
        self._history.append(cmd)
        self._history_ptr += 1

        # Для KeyCommand возвращаем текущий текст, для других - результат
        if isinstance(cmd, KeyCommand):
            return self._text_buffer.get_text()
        else:
            return result

    def undo(self) -> str:
        if self._history_ptr < 0:
            return "nothing to undo"

        cmd = self._history[self._history_ptr]
        result = cmd.undo()
        self._history_ptr -= 1

        # Для KeyCommand возвращаем текущий текст, для других - результат undo
        if isinstance(cmd, KeyCommand):
            return self._text_buffer.get_text()
        else:
            return result

    def redo(self) -> str:
        if self._history_ptr >= len(self._history) - 1:
            return "nothing to redo"

        self._history_ptr += 1
        cmd = self._history[self._history_ptr]
        result = cmd.redo()

        # Для KeyCommand возвращаем текущий текст, для других - результат redo
        if isinstance(cmd, KeyCommand):
            return self._text_buffer.get_text()
        else:
            return result

    def get_current_text(self) -> str:
        return self._text_buffer.get_text()


# =============================
# 5. СЕРИАЛИЗАЦИЯ
# =============================

class KeyboardSerializer:
    """Механизм сериализации/десериализации (независим от формата)"""

    def __init__(self, filename: str):
        self.filename = filename

    def serialize(self, keyboard: Keyboard) -> None:
        # Используем безопасный метод из Keyboard
        data = keyboard.get_key_binds_dict_for_save()  # возвращает Dict[str, Dict[str, Any]]
        with open(self.filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def deserialize(self) -> Dict[str, Any]:
        if not os.path.exists(self.filename):
            return {}
        with open(self.filename, 'r', encoding='utf-8') as f:
            return json.load(f)

# =============================
# 6. ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# =============================


# создание нужных файлов
def ensure_output_dir():
    out_dir = "lab6_output"
    os.makedirs(out_dir, exist_ok=True)
    return (
        os.path.join(out_dir, "console_output.txt"),
        os.path.join(out_dir, "journal.txt"),
        os.path.join(out_dir, "keyboard_state.json")
    )


def build_command_type_map() -> Dict[str, Type[Command]]:
    """
    Автоматически создаёт маппинг: "KeyCommand" → KeyCommand
    Ищет все подклассы Command, у которых есть атрибут command_type.
    """
    mapping = {}
    for cls in Command.__subclasses__():
        if hasattr(cls, 'command_type'):
            mapping[cls.command_type] = cls
    return mapping


# =============================
# 7. ДЕМОНСТРАЦИЯ
# =============================

def main():
    console_file, journal_file, state_file = ensure_output_dir()

    class DualOutput:
        def __init__(self, *files):
            self.files = files

        def write(self, s):
            for f in self.files:
                f.write(s)

        def flush(self):
            for f in self.files:
                f.flush()

    with open(console_file, 'w', encoding='utf-8') as cf:
        original = sys.stdout
        sys.stdout = DualOutput(original, cf)

        try:
            print("=" * 60)
            print("ЛАБОРАТОРНАЯ РАБОТА 6: ВИРТУАЛЬНАЯ КЛАВИАТУРА")
            print("=" * 60)

            text_buffer = TextBuffer()
            keyboard = Keyboard(text_buffer)
            serializer = KeyboardSerializer(state_file)

            # Загрузка
            raw_data = serializer.deserialize()  # возвращает dict[str, dict]
            if raw_data:
                command_type_map = build_command_type_map()

                for key, cmd_data in raw_data.items():
                    cmd_type = cmd_data["type"]

                    # Проверяем, известен ли такой тип
                    if cmd_type not in command_type_map:
                        raise ValueError(f"Неизвестная команда в файле: {cmd_type}")

                    # Получаем КЛАСС команды
                    command_class: Type[Command] = command_type_map[cmd_type]

                    # Создаём объект команды из данных
                    cmd = command_class.from_dict(cmd_data)

                    # Особый случай: KeyCommand требует buffer
                    if isinstance(cmd, KeyCommand):
                        cmd.set_buffer(text_buffer)

                    # Привязываем к клавише
                    keyboard.bind_key(key, cmd)
                print("Состояние клавиатуры загружено")
            else:
                # Создаём привязки по умолчанию
                default_binds = {
                    "a": KeyCommand("a", text_buffer),
                    "b": KeyCommand("b", text_buffer),
                    "c": KeyCommand("c", text_buffer),
                    "d": KeyCommand("d", text_buffer),
                    "ctrl++": VolumeUpCommand(20),
                    "ctrl+-": VolumeDownCommand(20),
                    "ctrl+p": MediaPlayerCommand(),
                }
                for k, cmd in default_binds.items():
                    keyboard.bind_key(k, cmd)
                print("Привязки по умолчанию созданы")

            # Сохраняем текущее состояние
            serializer.serialize(keyboard)

            text_buffer.clear()

            # Тестируем последовательность
            test_seq = [
                "a", "b", "c",
                "undo", "undo",
                "redo",
                "ctrl++",
                "ctrl+-",
                "ctrl+p",
                "d",
                "undo", "undo"
            ]

            print("\nВыполняемая последовательность:", " -> ".join(test_seq))
            print("\nРезультат (как в TEXT FILE):")

            # Журнал: только текущий текст после каждой операции
            with open(journal_file, 'w', encoding='utf-8') as journal:
                for action in test_seq:
                    if action == "undo":
                        log_line = keyboard.undo()
                    elif action == "redo":
                        log_line = keyboard.redo()
                    else:
                        log_line = keyboard.execute(action)

                    print(log_line)
                    journal.write(log_line + "\n")

            print(f"\nЖурнал сохранен в {journal_file}")
            print(f"Консольный вывод - в {console_file}")
            print(f"Состояние клавиатуры - в {state_file}")

        finally:
            sys.stdout = original

    print("\n" + "=" * 60)
    print("ГОТОВО! Проверьте папку lab6_output/")
    print("=" * 60)


if __name__ == "__main__":
    main()
