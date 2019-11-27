from hashlib import sha1
import requests

class DHTNode(object):
    # Static variables
    m = 256
    size = 2 ** DHTNode.m

    # Static methods
    @staticmethod
    def hash(x):
        return sha1(x)

    @staticmethod
    def address(host):
        return 'https://127.0.0.1:{:d}'.format(host)

    @staticmethod
    def distance(a, b):
        if a > b:
            return DHTNode.distance(b, a)
        return min(b - a, DHTNode.size + a - b)

    @staticmethod
    def between(x, a, b):
        if a > b:
            return not DHTNode.between(x, b, a)
        return x > a and x < b

    @staticmethod
    def partition(dictionary, pivot):
        below = list()
        above = list()

        for key, value in dictionary.items():
            if key <= pivot:
                below.append((key, value))
            else:
                above.append((key, value))

        return dict(below), dict(above)

    # Class methods
    def __init__(self, host):
        self.host = host
        self.id = hash(self.host)

        self.predecessor = self.host
        self.successor = self.host

        self.host_table =  set(self.host)
        self.hash_table = {}

    def join(self, host):
        url = address(host) + '/successor?{:d}'.format(self.id)
        self.update_successor(requests.get(url))

        url = address(self.successor) + '/predecessor?{:d}'.format(self.id)
        self.update_predecessor(requests.get(url))

        return # ok

    def update_successor(self, host):
        if host == self.successor:
            return # ok

        self.successor = host
        self.host_table.add(self.successor)
        below, above = DHTNode.partition(self.hash_table, self.id)

        url = address(self.successor) + '/transfer'
        resp = requests.post(url, table=above)
        if resp != 200:
            return # nok

        self.hash_table, _ = DHTNode.partition(self.hash_table, DHTNode.hash(self.successor))

        url = address(self.successor) + '/update_predecessor'
        resp = requests.post(url, host=self.host)

        return #ok

    def update_predecessor(self, host):
        if host == self.predecessor:
            return # ok

        self.predecessor = host
        self.host_table.add(self.predecessor)
        below, above = DHTNode.partition(self.hash_table, self.id)

        url = address(self.predecessor) + '/transfer'
        resp = requests.post(url, table=below)
        if resp != 200:
            return # nok

        _, self.hash_table = DHTNode.partition(self.hash_table, DHTNode.hash(self.predecessor))

        url = address(self.predecessor) + '/update_successor'
        resp = requests.post(url, host=self.host)

        return #ok

    def predecessor(self, key):
        host = self.lookup(key)[0]
        url = address(host) + '/node_predecessor'
        rest = requests.get(url)
        return resp

    def successor(self, key):
        return self.lookup(key)[0]

    def node_predecessor(self):
        return self.predecessor

    def node_successor(self):
        return self.successor

    def lookup(self, key):
        id_p = DHTNode.hash(self.predecessor)
        id_s = DHTNode.hash(self.successor)

        if key == id_p:
            resp = requests.get(address(self.predecessor))
            if resp.status_code != 200:
                self.host_table.remove(self.predecessor)
                # update_predecessor
            else:
                chain = [self.predecessor]
        elif key == self.id or DHTNode.between(key, id_p, self.id):
            chain = []
        elif key == id_s or DHTNode.between(key, self.id, id_s):
            resp = requests.get(address(self.successor))
            if resp.status_code != 200:
                self.host_table.remove(self.successor)
                # update_successor
            else:
                chain = [self.successor]
        else:
            while True:
                host = min(
                    self.host_table,
                    key=lambda x: DHTNode.distance(DHTNode.hash(x), key)
                )

                if host is self.host:
                    return # nok

                resp = requests.get(address(host))
                if resp.status_code != 200:
                    self.host_table.remove(host)
                else:
                    break

            url = address(host) + '/lookup?{:d}'.format(key)
            chain = requests.get(url)

            self.host_table |= set(chain)

        return chain + [self.host]

    def exists(self, key):
        host = lookup(key)[0]

        if host == self.host:
            if key in self.hash_table:
                return True
            else:
                return False
        else:
            url = address(host) + '/exists?{:d}'.format(key)
            rest = requests.get(url)
            return resp

    def get(self, key):
        host = lookup(key)[0]

        if host == self.host:
            if key in self.hash_table:
                return self.hash_table[key]
            else:
                return # nok
        else:
            url = address(host) + '/get?{:d}'.format(key)
            rest = requests.get(url)
            return resp

    def put(self, key, value):
        host = lookup(key)[0]

        if host == self.host:
            if key in self.hash_table:
                return # nok
            else:
                self.hash_table[key] = value
        else:
            url = address(host) + '/put'
            rest = requests.post(url, key=key, value=value)
            return resp

    def copy(self, src_key, dst_key)
        value = self.get(src_key) # try catch
        self.put(dst_key, value) # try catch

        return # ok
