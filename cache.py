class Memcached(object):

    def __init__(self, servers, username, password, timeout=0):

        import pylibmc
        self.conn = pylibmc.Client(servers, username=username, password=password)
        self.timeout = timeout

    def __getitem__(self, key):
        return self.conn.get(key)

    def __setitem__(self, key, value):
        self.conn.set(key, value, time=self.timeout)


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
