
import collections


class Environment(collections.MutableMapping):
    def __init__(self, **namespace):
        self.namespace = namespace

    def __getitem__(self, key):
        return self.namespace[key]

    def __setitem__(self, key, value):
        self.namespace[key] = value

    def __delitem__(self, key):
        del self.namespace[key]

    def __len__(self):
        return len(self.namespace)

    def __iter__(self):
        return iter(self.namespace)
