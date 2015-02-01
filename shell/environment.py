
import collections


class LookupError(Exception):
    pass


class WriteForbidden(LookupError):
    pass


class DeleteForbidden(LookupError):
    pass


class Lookup:
    def __init__(self, getter=None, setter=None, deleter=None):
        if getter is not None:
            self.__get__ = getter
        if setter is not None:
            self.__set__ = setter
        if deleter is not None:
            self.__delete__ = deleter

    def setter(self, function):
        self.__set__ = function

    def deleter(self, function):
        self.__delete__ = function

    def __get__(self):
        pass

    def __set__(self, new):
        raise WriteForbidden

    def __delete__(self):
        raise DeleteForbidden


class NO_DEFAULT:
    pass


class ItemLookup(Lookup):
    def __init__(self, obj, item, default=NO_DEFAULT,
                 set_allowed=True, delete_allowed=True):
        self.obj = obj
        self.item = item
        self.default = default
        self.set_allowed = set_allowed
        self.delete_allowed = delete_allowed

    def __get__(self):
        if self.default is NO_DEFAULT:
            return self.obj[self.item]
        else:
            return self.obj.get(self.item, self.default)

    def __set__(self, new):
        if self.set_allowed:
            self.obj[self.item] = new
        else:
            raise WriteForbidden

    def __delete__(self):
        if self.delete_allowed:
            del self.obj[self.item]
        else:
            raise DeleteForbidden


class AttributeLookup(Lookup):
    def __init__(self, obj, attr, default=NO_DEFAULT,
                 set_allowed=True, delete_allowed=True):
        self.obj = obj
        self.attr = attr
        self.default = default
        self.set_allowed = set_allowed
        self.delete_allowed = delete_allowed

    def __get__(self):
        if self.default is NO_DEFAULT:
            return getattr(self.obj, self.attr)
        else:
            return getattr(self.obj, self.attr, self.default)

    def __set__(self, new):
        if self.set_allowed:
            setattr(self.obj, self.attr, new)
        else:
            raise WriteForbidden

    def __delete__(self):
        if self.delete_allowed:
            delattr(self.obj, self.attr)
        else:
            raise DeleteForbidden


class Environment(collections.MutableMapping):
    """

    >>> source_list = [1, 2, 3]

    >>> source_dict = {'b': 5}

    >>> class MyClass:
    ...   def __init__(self, property):
    ...     self.property = property

    >>> source_object = MyClass(6)

    >>> def source_callable():
    ...   return 'Generated Value'

    >>> env = Environment(
    ...   first = ItemLookup(source_list, 0),
    ...   zero = ItemLookup(source_list, 0, delete_allowed=False),
    ...   a = ItemLookup(source_dict, 'a', default='default'),
    ...   b = ItemLookup(source_dict, 'b'),
    ...   property = AttributeLookup(source_object, 'property'),
    ...   gen = Lookup(source_callable),
    ... )

    >>> env['zero']
    1

    >>> del env['zero']
    Traceback (most recent call last):
     ...
    DeleteForbidden

    >>> del env['first']

    >>> env['first']
    2

    >>> env['a']
    'default'

    >>> env['a'] = 9

    >>> env['a']
    9

    >>> del env['a']

    >>> env['a']
    'default'

    >>> env['b']
    5

    >>> del env['b']

    >>> env['b']
    Traceback (most recent call last):
     ...
    KeyError: 'b'

    >>> env['gen']
    'Generated Value'

    >>> env['gen'] = 'x'
    Traceback (most recent call last):
     ...
    WriteForbidden
    """
    def __init__(self, **namespace):
        self.namespace = dict()
        self.namespace.update(namespace)

    def __getitem__(self, key):
        value = self.namespace[key]
        if isinstance(value, Lookup):
            return value.__get__()
        return value

    def __setitem__(self, key, value):
        if isinstance(value, Lookup):
            self.namespace[key] = value
        else:
            lookup = self.namespace.get(key)
            if isinstance(lookup, Lookup):
                lookup.__set__(value)
            else:
                self.namespace[key] = value

    def __delitem__(self, key):
        lookup = self.namespace.get(key)
        if isinstance(lookup, Lookup):
            lookup.__delete__()
        else:
            del self.namespace[key]

    def __len__(self):
        return len(self.namespace)

    def __iter__(self):
        return iter(self.namespace)


if __name__ == '__main__':
    import doctest
    doctest.testmod()
