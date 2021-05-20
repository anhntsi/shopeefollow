from dataclasses import dataclass


class Base:
    def get_key(self) -> str:
        ...


@dataclass
class Class(Base):
    type_: type
    key: str

    def get_key(self) -> str:
        return self.key

    def __repr__(self):
        return f"Class<key=\"{self.key}\", type={self.type_}>"


@dataclass
class Typed(Base):

    var_type: type
    key: str

    def get_key(self) -> str:
        return self.key

    def __call__(self, *args, **kwargs):
        return self.var_type(*args, **kwargs)

    def __repr__(self):
        return f"Typed<type={self.var_type}, key=\"{self.key}\">"


class List(Class):
    ...


def hookable(class_: type):
    """
    :param class_: the class
    :return: the same class without constructor
    by removing the class constructor, this makes it possible for the class to be hooked.
    I know this is a bad idea but there is no other way to create a class without calling the constructor
    """
    class_.__init__ = lambda self: None

    return class_


def by_name(class_: type):
    """
    :param class_: the class
    :return: the same class with the attribute assigned the key by name
    """
    for key, value in class_.__annotations__.items():
        if not isinstance(value, Base) and type(value) == type and value.__module__ == "builtins":
            class_.__annotations__[key] = Typed(value, key)
        elif value in (None, ...):
            class_.__annotations__[key] = key

    return class_


def objhook(objtype: type, data: dict, recursive_class_hook: bool = True, type_check: bool = False,
            str_hook: bool = True):
    """
    :param objtype: class(type not instance) to hook
    :param data: data that will be inserted into the class instance
    :param recursive_class_hook: allow entering data recursively into the class using Class
    :param type_check: allow type checking
    :param str_hook: use strings as key
    :return: the result
    """
    output = objtype()
    for key, value in output.__annotations__.items():
        value_type = type(value)
        if value_type == str:
            if str_hook and value in data:
                setattr(output, key, data[value])
        elif isinstance(value, Base):
            value: Base
            data_key = value.get_key()
            if data_key in data:
                data_value = data[data_key]
                if value_type == Typed:
                    value: Typed
                    if type_check and (type(data_value) not in (value.var_type, type(None))):
                        raise TypeError(f"Incompatible type:\n{key}: {value}\n{data_key}: {data_value}")
                    setattr(output, key, data_value)
                elif value_type == Class and recursive_class_hook:
                    value: Class
                    if data_value is not None:
                        setattr(output, key, objhook(value.type_, data[data_key], recursive_class_hook, type_check,
                                                     str_hook))
                    else:
                        setattr(output, key, None)
                elif value_type == List:
                    value: List
                    if data_value is not None:
                        setattr(output, key, [])
                        for item in data_value:
                            getattr(output, key).append(objhook(value.type_, item, recursive_class_hook, type_check,
                                                                str_hook))
                    else:
                        setattr(output, key, None)

    return output
