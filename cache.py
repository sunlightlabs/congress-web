class Memcached(object):

    def __init__(self, servers, username, password, timeout=None):

        import pylibmc
        self.conn = pylibmc.Client(servers, username=username, password=password)
        self.timeout = None

    def __getitem__(self, key):
        pass

    def __setitem__(self, key, value):
        pass


class Dummycached(object):

    def __getitem__(self, key):
        pass  # nope!

    def __setitem__(self, key, value):
        pass  # nope!


class Dictcached(object):

    def __init__(self):
        self._cache = {}

    def __getitem__(self, key):
        return self._cache.get(key)

    def __setitem__(self, key, value):
        self._cache[key] = value
