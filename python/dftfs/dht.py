from hashlib import sha1
import requests

class DHTNode(object):
    # Static variables
    M = 2 ** 32

    # Static methods
    @staticmethod
    def hash(x):
        return sha1(x) % DHTNode.M

    @staticmethod
    def address(host):
        return 'https://127.0.0.1:{:d}'.format(host)

    @staticmethod
    def distance(a, b):
        if a > b:
            return M - distance(b, a)
        return b - a

    @staticmethod
    def between(a, b, c):
        return distance(a, b) + distance(b, c) == distance(a, c)

    # Class methods
    def __init__(self, host):
        self.host = host
        self.id = hash(self.host)

        self.predecessor = (self.id, self.host)
        self.successor = (self.id, self.host)

        self.host_table = {}
        self.hash_table = {}

    def join(self, host):
        url = address(host) + '/lookup?{:d}'.format(self.id)
        successor = requests.get(url)[0]

        url = address(successor) + '/predecessor'
        predecessor = requests.get(url)

        self.update_predecessor(predecessor)
        self.update_successor(successor)

    def update_successor(self, host):
        if self.successor[1] != host:
            old = self.successor
            self.successor = (hash(host), host)
            self.hash_table[self.successor[0]] = self.successor[1]

            # Inform successor
            url = address(self.successor[1]) + '/update_predecessor'
            resp = requests.post(url, host=self.host)

    def update_predecessor(self, host):
        if self.predecessor[1] != host:
            old = self.predecessor
            self.predecessor = (hash(host), host)

            # Inform predecessor
            url = address(self.predecessor[1]) + '/update_successor'
            resp = requests.post(url, host=self.host)

            # Give responsability
            if DHTNode.between(self.predecessor[0], old[0], self.id):
                url = address(self.predecessor) + '/put'
                for key, value in *hash_table: # del while iterating
                    if DHTNode.between(key, old[0], self.predecessor[0]):
                        resp = requests.post(url, key=value, value=value)
                        del hash_table[key]

    def stabilize(self, chain):
        for host in chain:
            if host is not None:
                self.hash_table[DHTNode.bash(host)] = host

    def lookup(self, key):
        if key == self.id or DHTNode.between(self.predecessor[0], key, self.id):
            chain = []
        else:
            while True:
                id, host = min(
                    self.host_table,
                    key=lambda x: DHTNode.distance(x[0], key)
                )

                url = address(host)
                resp = requests.get(url)

                if resp.status_code != 200:
                    if host == self.successor[1]:
                        chain = [None]
                        break

                    del self.hash_table[id]
                else:
                    url = address(host) + '/lookup?{:d}'.format(key)
                    chain = requests.get(url)                  
                    break

        self.stabilize(chain)

        return chain + [self.host]

    def exists(self, key):
        if key in self.hash_table:
            return True
        else:
            return False

    def get(self, key):
        if self.exists(key):
            return self.hash_table[key]
        else:
            return # nok

    def put(self, key, value):
        if self.exists(key):
            return # nok
        else:
            self.hash_table[key] = value
