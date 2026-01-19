import abc
from contextlib import contextmanager
from typing import (
    Any,
    Callable,
    Dict,
    Optional,
    Type,
    Union,
    get_type_hints
)
from enum import Enum


# ========== Часть 1: DI контейнер ==========

class LifeStyle(Enum):
    PerRequest = "PerRequest" # Новый объект при каждом вызове
    Scoped = "Scoped" # Один объект на один "контекст" (например, внутри `with`)
    Singleton = "Singleton" # Один объект на всю программу


class InjectorAlreadyConfiguredError(Exception):
    pass


class UnregisteredDependencyError(Exception):
    pass


class Injector:
    def __init__(self):
        self._registrations: Dict[Type, Dict[str, Any]] = {}
        self._singleton_cache: Dict[Type, Any] = {}
        self._scoped_cache: Optional[Dict[Type, Any]] = None
        self._in_scope = False

    def register(
        self,
        interface_type: Type,
        class_type: Union[Type, Callable[[], Any], None] = None,
        life_style: Optional[LifeStyle] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Регистрирует зависимость.
        Возможны два режима:
        1. register(interface, factory_function)
        2. register(interface, ConcreteClass, LifeStyle.XXX, params={...})
        """
        if self._in_scope:
            raise InjectorAlreadyConfiguredError("Нельзя регистрировать зависимости во время scope.")

        # Случай 1: фабричная функция
        if callable(class_type) and life_style is None:
            registration = {
                "class_type": class_type,
                "life_style": None,
                "params": params or {},
                "is_factory": True,
            }
        # Случай 2: класс-реализация
        elif class_type is not None and isinstance(class_type, type) and life_style is not None:
            if not issubclass(class_type, interface_type):
                raise TypeError(f"{class_type.__name__} не реализует {interface_type.__name__}")
            registration = {
                "class_type": class_type,
                "life_style": life_style,
                "params": params or {},
                "is_factory": False,
            }
        else:
            raise ValueError(
                "Неверные аргументы регистрации. Возможны два варианта:\n"
                "1. register(interface, factory_function)\n"
                "2. register(interface, ConcreteClass, LifeStyle.SINGLETON, params={...})"
            )

        self._registrations[interface_type] = registration

    def _resolve_constructor_dependencies(self, cls: Type) -> Dict[str, Any]:
        """Автоматически разрешает (resolve) зависимости по ТИПУ параметров __init__."""
        deps = {}
        try:
            hints = get_type_hints(cls.__init__)
        except Exception:
            hints = {}

        for param_name, param_type in hints.items():
            if param_name == "self":
                continue

            if param_type in self._registrations:
                deps[param_name] = self.get_instance(param_type)
            elif param_name in self._get_active_params():
                deps[param_name] = self._get_active_params()[param_name]
            else:
                raise UnregisteredDependencyError(
                    f"Не могу разрешить параметр '{param_name}' (тип: {param_type}) "
                    f"в конструкторе {cls.__name__}. "
                    f"Зарегистрируйте интерфейс {param_type} или передайте параметр вручную."
                )
        return deps

    def _get_active_params(self) -> Dict[str, Any]:
        params = {}
        for reg in self._registrations.values():
            custom_params = reg.get("params")
            if custom_params:
                params.update(custom_params)
        return params

    def get_instance(self, interface_type: Type) -> Any:
        if interface_type not in self._registrations:
            raise UnregisteredDependencyError(f"Интерфейс {interface_type} не зарегистрирован.")

        reg = self._registrations[interface_type]
        life_style = reg["life_style"]
        is_factory = reg.get("is_factory", False)

        if is_factory:
            factory = reg["class_type"]
            return factory()

        if life_style == LifeStyle.Singleton:
            if interface_type in self._singleton_cache:
                return self._singleton_cache[interface_type]
            instance = self._create_instance(interface_type)
            self._singleton_cache[interface_type] = instance
            return instance

        if life_style == LifeStyle.Scoped:
            if self._scoped_cache is None:
                raise RuntimeError("Scoped-объекты можно получать только внутри scope.")
            if interface_type in self._scoped_cache:
                return self._scoped_cache[interface_type]
            instance = self._create_instance(interface_type)
            self._scoped_cache[interface_type] = instance
            return instance

        if life_style == LifeStyle.PerRequest:
            return self._create_instance(interface_type)

        raise ValueError(f"Неизвестный стиль жизни: {life_style}")

    def _create_instance(self, interface_type: Type) -> Any:
        reg = self._registrations[interface_type]
        cls = reg["class_type"]
        manual_params = reg["params"]
        resolved_deps = self._resolve_constructor_dependencies(cls)
        resolved_deps.update(manual_params)
        return cls(**resolved_deps)

    @contextmanager
    def scope(self):
        if self._in_scope:
            raise RuntimeError("Вложенные scope не поддерживаются.")
        self._in_scope = True
        self._scoped_cache = {}
        try:
            yield self
        finally:
            self._scoped_cache = None
            self._in_scope = False


# ========== Часть 2: Интерфейсы и реализации ==========

class Interface1(abc.ABC):
    @abc.abstractmethod
    def do_something(self) -> str:
        pass


class Interface2(abc.ABC):
    @abc.abstractmethod
    def process(self) -> str:
        pass


class Interface3(abc.ABC):
    @abc.abstractmethod
    def log(self, message: str) -> str:
        pass


# --- Реализации Interface1 ---
class Class1Debug(Interface1):
    def __init__(self, logger: Interface3):
        self.logger = logger

    def do_something(self) -> str:
        msg = "Debug mode: doing something..."
        return self.logger.log(msg)


class Class1Release(Interface1):
    def do_something(self) -> str:
        return "Release mode: done!"


# --- Реализации Interface2 ---
class Class2Debug(Interface2):
    def __init__(self, logger: Interface3):
        self.logger = logger

    def process(self) -> str:
        msg = "Debug mode: processing..."
        return self.logger.log(msg)


class Class2Release(Interface2):
    def process(self) -> str:
        return "Release mode: processed!"


# --- Реализации Interface3 ---
class Class3Debug(Interface3):
    def log(self, message: str) -> str:
        return f"[DEBUG] {message}"


class Class3Release(Interface3):
    def log(self, message: str) -> str:
        return f"[RELEASE] {message}"


# ========== Часть 3: Конфигурации ==========

def configure_debug(injector: Injector):
    injector.register(Interface3, Class3Debug, LifeStyle.Singleton)
    injector.register(Interface1, Class1Debug, LifeStyle.Scoped)
    injector.register(Interface2, Class2Debug, LifeStyle.PerRequest)


def configure_release(injector: Injector):
    injector.register(Interface3, Class3Release, LifeStyle.Singleton)
    injector.register(Interface1, Class1Release, LifeStyle.Singleton)
    injector.register(Interface2, Class2Release, LifeStyle.PerRequest)


# ========== Часть 4: Демонстрация ==========

def demo_configuration(name: str, configure_func: Callable[[Injector], None]):
    print(f"{'='*50}")
    print(f"ДЕМОНСТРАЦИЯ: {name}")
    print('='*50)

    injector = Injector()
    configure_func(injector)

    # Singleton — всегда один и тот же
    print("\n→ Singleton (Interface3):")
    log1 = injector.get_instance(Interface3)
    log2 = injector.get_instance(Interface3)
    print(f"  log1 == log2: {log1 is log2}")

    # PerRequest — каждый раз новый
    print("\n→ PerRequest (Interface2):")
    proc1 = injector.get_instance(Interface2)
    proc2 = injector.get_instance(Interface2)
    print(f"  proc1 == proc2: {proc1 is proc2}")

    # Scoped — один в пределах scope
    print("\n→ Scoped (Interface1) — вне scope (ошибка):")
    try:
        injector.get_instance(Interface1)
    except RuntimeError as e:
        print(f"  Ошибка (ожидаемо): {e}")

    print("\n→ Scoped (Interface1) — внутри scope:")
    with injector.scope() as scoped_inj:
        obj1 = scoped_inj.get_instance(Interface1)
        obj2 = scoped_inj.get_instance(Interface1)
        print(f"  obj1 == obj2: {obj1 is obj2}")

        # Проверим работу через зависимости
        print("\n→ Использование через интерфейсы:")
        print(f"  Interface1: {obj1.do_something()}")
        print(f"  Interface2: {scoped_inj.get_instance(Interface2).process()}")

    # После выхода из scope — нельзя
    print("\n→ Scoped — после выхода из scope:")
    try:
        injector.get_instance(Interface1)
    except RuntimeError as e:
        print(f"  Ошибка (ожидаемо): {e}")

    # Фабричный метод
    print("\n→ Фабричный метод:")

    def factory_interface3():
        return Class3Debug()

    injector2 = Injector()
    injector2.register(Interface3, factory_interface3)
    log_f = injector2.get_instance(Interface3)
    print(f"  Фабрика вернула: {log_f.log('hello from factory')}")


if __name__ == "__main__":
    demo_configuration("ОТЛАДОЧНАЯ КОНФИГУРАЦИЯ", configure_debug)
    demo_configuration("РЕЛИЗНАЯ КОНФИГУРАЦИЯ", configure_release)
