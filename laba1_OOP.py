import math
from typing import Self
TOL = 1e-10
U_SIGN = 'U'
EMPTY_PLENTY_SIGN = "∅"


class Angle:
    """Класс для хранения и работы с углами"""
    def __init__(self, radians: float) -> None:
        # Основной конструктор - принимает только радианы
        self._radians = self._normalize(radians)

    @classmethod
    def from_degrees(cls, degrees: float) -> Self:
        # Альтернативный конструктор - создает Angle из градусов
        radians = math.radians(degrees)
        return cls(radians)

    @property
    def radians(self):
        """Получить угол в радианах"""
        return self._radians

    @radians.setter
    def radians(self, value):
        """Установить угол в радианах"""
        self._radians = self._normalize(value)

    @property
    def degrees(self):
        """Получить угол в градусах"""
        return math.degrees(self._radians)

    @degrees.setter
    def degrees(self, value):
        """Установить угол в градусах"""
        self._radians = math.radians(value)

    @staticmethod
    def _normalize(radians):
        """Нормализовать угол в диапазон [0, 2π)"""
        two_pi = 2 * math.pi
        normalized = radians % two_pi
        if normalized < 0:
            normalized += two_pi
        return normalized

    def __float__(self):
        """Преобразование в float (в радианах)"""
        return self._radians

    def __int__(self):
        """Преобразование в int (в радианах, округление)"""
        return int(round(self._radians))

    def __str__(self):
        """Строковое представление"""
        return f"{self.degrees:.2f}°"

    def __repr__(self):
        """Представление для отладки"""
        return f"Angle(radians={self._radians:.6f})"

    def __eq__(self, other):
        """Сравнение на равенство"""
        if isinstance(other, (int, float)):
            other = Angle(other)
        if isinstance(other, Angle):
            return abs(self._radians - other._radians) < TOL
        return NotImplemented

    def __lt__(self, other):
        """Меньше"""
        if isinstance(other, (int, float)):
            other = Angle(other)
        if isinstance(other, Angle):
            return self._radians < other._radians
        return NotImplemented

    def __le__(self, other):
        """Меньше или равно"""
        if isinstance(other, (int, float)):
            other = Angle(other)
        if isinstance(other, Angle):
            return self._radians <= other._radians
        return NotImplemented

    def __gt__(self, other):
        """Больше"""
        return not self <= other

    def __ge__(self, other):
        """Больше или равно"""
        return not self < other

    def __add__(self, other):
        """Сложение"""
        if isinstance(other, (int, float)):
            return Angle(self._radians + other)
        if isinstance(other, Angle):
            return Angle(self._radians + other._radians)
        return NotImplemented

    def __radd__(self, other):
        """Правое сложение"""
        return self.__add__(other)

    def __sub__(self, other):
        """Вычитание"""
        if isinstance(other, (int, float)):
            return Angle(self._radians - other)
        if isinstance(other, Angle):
            return Angle(self._radians - other._radians)
        return NotImplemented

    def __rsub__(self, other):
        """Правое вычитание"""
        if isinstance(other, (int, float)):
            return Angle(other - self._radians)
        return NotImplemented

    def __mul__(self, scalar):
        """Умножение на скаляр"""
        if isinstance(scalar, (int, float)):
            return Angle(self._radians * scalar)
        return NotImplemented

    def __rmul__(self, scalar):
        """Правое умножение на скаляр"""
        return self.__mul__(scalar)

    def __truediv__(self, scalar):
        """Деление на скаляр"""
        if isinstance(scalar, (int, float)):
            if scalar == 0:
                raise ZeroDivisionError("Division by zero")
            return Angle(self._radians / scalar)
        return NotImplemented

    def __abs__(self):
        """Абсолютное значение"""
        return Angle(abs(self._radians))


class AngleRange:
    """Класс для хранения промежутков углов"""
    def __init__(self, start, end, start_inclusive=True, end_inclusive=True):

        self.start = self._to_angle(start)
        self.end = self._to_angle(end)
        self.start_inclusive = start_inclusive
        self.end_inclusive = end_inclusive

    @classmethod
    def from_degrees(cls, start_deg: float, end_deg: float,
                     start_inclusive: bool = True, end_inclusive: bool = True) -> Self:
        start = Angle.from_degrees(start_deg)
        end = Angle.from_degrees(end_deg)
        return cls(start, end, start_inclusive, end_inclusive)

    @staticmethod
    def _to_angle(value):
        """Преобразование в Angle"""
        if isinstance(value, Angle):
            return value
        elif isinstance(value, (int, float)):
            return Angle(value)
        else:
            raise TypeError("Value must be Angle, int or float")

    def __eq__(self, other):
        """Сравнение на равенство"""
        if not isinstance(other, AngleRange):
            return False
        return (self.start == other.start and
                self.end == other.end and
                self.start_inclusive == other.start_inclusive and
                self.end_inclusive == other.end_inclusive)

    def __str__(self):
        """Строковое представление"""
        start_bracket = '[' if self.start_inclusive else '('
        end_bracket = ']' if self.end_inclusive else ')'
        return f"{start_bracket}{self.start}, {self.end}{end_bracket}"

    def __repr__(self):
        """Представление для отладки"""
        return (f"AngleRange(start={self.start!r}, end={self.end!r}, "
                f"start_inclusive={self.start_inclusive}, end_inclusive={self.end_inclusive})")

    def __abs__(self):
        """Длина промежутка"""
        if self.start <= self.end:
            return Angle(self.end.radians - self.start.radians)
        else:
            # Промежуток проходит через 0
            return Angle(2 * math.pi - self.start.radians + self.end.radians)

    def __contains__(self, item):
        """Проверка принадлежности угла или промежутка"""
        if isinstance(item, (Angle, int, float)):
            angle = self._to_angle(item)
            return self._contains_angle(angle)
        elif isinstance(item, AngleRange):
            return self._contains_range(item)
        else:
            return False

    def _contains_angle(self, angle):
        """Проверка принадлежности угла"""
        if self.start <= self.end:
            # Обычный промежуток
            left_ok = (angle > self.start) or (angle == self.start and self.start_inclusive)
            right_ok = (angle < self.end) or (angle == self.end and self.end_inclusive)
            return left_ok and right_ok
        else:
            # Промежуток проходит через 0
            left_ok = (angle > self.start) or (angle == self.start and self.start_inclusive)
            right_ok = (angle < self.end) or (angle == self.end and self.end_inclusive)
            return left_ok or right_ok

    def _contains_range(self, other):
        """Проверка вхождения промежутка в другой"""
        # Упрощенная проверка - точное совпадение границ
        return (self.start == other.start and self.end == other.end and
                (not other.start_inclusive or self.start_inclusive) and
                (not other.end_inclusive or self.end_inclusive))

    # region magic methods

    def __add__(self, other):
        """Объединение промежутков"""
        if not isinstance(other, AngleRange):
            return NotImplemented

        # Проверяем пересечение промежутков
        if self._intersects(other):
            # Если пересекаются - создаем объединенный промежуток
            new_start = min(self.start, other.start)
            new_end = max(self.end, other.end)
            return AngleRange(new_start, new_end)
        else:
            # Если не пересекаются - возвращаем строку с описанием
            return f"{self} {U_SIGN} {other}"

    def __sub__(self, other):
        """Разность промежутков"""
        if not isinstance(other, AngleRange):
            return NotImplemented

        if (self.start == other.start and self.end == other.end and
                (self.start_inclusive != other.start_inclusive or
                 self.end_inclusive != other.end_inclusive)):

            result = []
            if self.start_inclusive and not other.start_inclusive:
                result.append(str(self.start))

            if self.end_inclusive and not other.end_inclusive:
                if len(result) != 0:
                    result.append(f' {U_SIGN} ')
                result.append(str(self.end))

            return ''.join(result)

        if self == other:
            # Полное совпадение - пустое множество
            return EMPTY_PLENTY_SIGN

        if self._intersects(other):
            # Частичное пересечение
            part1 = AngleRange(self.start, other.start,
                               self.start_inclusive, not other.start_inclusive)
            part2 = AngleRange(other.end, self.end,
                               not other.end_inclusive, self.end_inclusive)

            result = []
            if part1.start.radians <= part1.end.radians and abs(part1) > TOL:
                result.append(str(part1))
            if part2.start.radians <= part2.end.radians and abs(part2) > TOL:
                if len(result) != 0:
                    result.append(f' {U_SIGN} ')
                result.append(str(part2))
            return ''.join(result)

        # Нет пересечения - возвращаем исходный промежуток
        return [self]

    def _intersects(self, other):
        """Проверяет, пересекаются ли промежутки"""
        # Простая проверка пересечения
        if self.start <= self.end and other.start <= other.end:
            # Оба обычных диапазона
            return not (self.end < other.start or other.end < self.start)
        else:
            return True


# Демонстрация работы классов
print("=== Демонстрация класса Angle ===")

# Создание углов
angle1 = Angle.from_degrees(45)  # 45 градусов
angle2 = Angle(math.pi / 4)  # π/4 радиан
angle3 = Angle.from_degrees(90)

print(f"angle1: {angle1} ({angle1.radians:.4f} рад)")
print(f"angle2: {angle2} ({angle2.radians:.4f} рад)")
print(f"angle3: {angle3} ({angle3.radians:.4f} рад)\n")

# Сравнение
print(f"{angle1} == {angle2}: {angle1 == angle2}")
print(f"{angle1} < {angle3}: {angle1 < angle3}\n")

# Арифметические операции
sum_angle = angle1 + angle3
diff_angle = angle3 - angle1
scaled_angle = angle1 * 2

print(f"{angle1} + {angle3} = {sum_angle}")
print(f"{angle3} - {angle1} = {diff_angle}")
print(f"{angle1} * 2 = {scaled_angle}\n")

# Преобразования
print(f"float(angle1): {float(angle1):.4f}")
print(f"int(angle1): {int(angle1)}")
print(f"str(angle1): {str(angle1)}\n")

print("=== Демонстрация класса AngleRange ===")

# Создание промежутков
range1 = AngleRange(0, math.pi / 2)  # [0°, 90°]
range2 = AngleRange.from_degrees(45, 135)
range3 = AngleRange.from_degrees(270, 90)  # Промежуток через 0
range4 = AngleRange.from_degrees(10, 90)
range5 = AngleRange.from_degrees(30, 60, False, False)

print(f"range1: {range1}")
print(f"range2: {range2}")
print(f"range3: {range3}")
print(f"Длина range1: {abs(range1)}")
print(f"Длина range2: {abs(range2)}")
print(f"Длина range3: {abs(range3)}\n")

# Проверка принадлежности
test_angle = Angle.from_degrees(60)
print(f"{test_angle} in {range1}: {test_angle in range1}")
print(f"{test_angle} in {range4}: {test_angle in range4}\n")

# Сравнение промежутков
print(f"{range1} == {range2}: {range1 == range2}\n")

# Операции с промежутками
print(f"{range5} + {range1} = {range4 + range1}")
print(f"{range4} - {range5} = {range4 - range5}")
