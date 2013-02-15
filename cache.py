class Memcached(object):

    def __init__(self, servers, username=None, password=None, timeout=0):

        import pylibmc
        self.conn = pylibmc.Client(servers, binary=True, username=username, password=password)
        self.timeout = timeout

    def __getitem__(self, key):
        key = key.encode('utf-8', errors='ignore')
        return self.conn.get(key)

    def __setitem__(self, key, value):
        key = key.encode('utf-8', errors='ignore')
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
