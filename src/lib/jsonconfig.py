import os
from json import load, dumps

class JsonConfig:
    def __init__(self, slot = "/config", name = "settings"):
        self._slot = slot
        self._name = name
        self._path = '%s/%s.json' % (slot, name)
        self._dict = {}
        self.reload()

    @property
    def dict(self):
        return self._dict

    def reload(self):
        try:
            with open(self._path, 'r') as json:
                self._dict = load(json)
        except:
            self._dict = {}

    def save(self):
        try:
            json = dumps(self._dict)
            try:
                os.mkdir(self._slot)
            except :
                pass
            file = open(self._path, 'wb')
            file.write(json)
            file.close()
            return True
        except :
            return False
