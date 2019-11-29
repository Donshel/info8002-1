from hashlib import sha1
import requests

# Parameters
size = 2 ** 32
replication = 3

# Methods
def hash(x):
    return int(int.from_bytes(sha1(str(x).encode()).digest(), 'big') % size)

def address(host):
    return 'http://127.0.0.1:{:d}/'.format(host)

# Node class
class DHTNode(object):
    # Static methods
    @staticmethod
    def distance(a, b):
        if a > b:
            return size - DHTNode.distance(b, a)
        return b - a

    @staticmethod
    def between(a, b, c):
        return a == c or DHTNode.distance(a, b) + DHTNode.distance(b, c) == DHTNode.distance(a, c)

    # Class methods
    def __init__(self, host):
        self.host = host
        self.id = hash(self.host)

        self.predecessor = (self.id, self.host)
        self.successor = (self.id, self.host)

        self.host_table = {}
        self.hash_table = {}

    def join(self, host):
        # Ping host
        url = address(host)
        resp = requests.get(url)

        if resp.status_code != 200:
            raise ProcessLookupError(resp.text, resp.status_code)

        # Lookup successor
        url = address(host) + 'lookup/{:d}/0'.format(self.id)
        resp = requests.get(url)

        if resp.status_code != 200:
            raise RuntimeError(resp.text, resp.status_code)

        successor = int(resp.text.split('\n')[0])

        # Get its predecessor
        url = address(successor) + 'predecessor'
        resp = requests.get(url)

        if resp.status_code != 200:
            raise RuntimeError(resp.text, resp.status_code)

        predecessor = int(resp.text)

        # Inform predecessor and successor
        url = address(predecessor) + 'update_successor/{:d}'.format(self.host)
        resp = requests.get(url)

        if resp.status_code != 200:
            raise RuntimeError(resp.text, resp.status_code)

        url = address(successor) + 'update_predecessor/{:d}'.format(self.host)
        resp = requests.get(url)

        if resp.status_code != 200:
            raise RuntimeError(resp.text, resp.status_code)

        # Update predecessor and successor
        self.update_successor(successor)
        self.update_predecessor(predecessor)

    def update_predecessor(self, host):
        old = self.predecessor
        self.predecessor = (hash(host), host)

        # Give responsability
        if DHTNode.between(old[0], self.predecessor[0], self.id):
            url = address(self.predecessor[1]) + 'put'
            for key, value in list(self.hash_table.items()):
                if DHTNode.between(old[0], key, self.predecessor[0]):
                    resp = requests.post(url, key=key, value=value)

                    if resp.status_code != 200:
                        raise RuntimeError(resp.text, resp.status_code)

                    del self.hash_table[key]

    def update_successor(self, host):
        old = self.successor
        self.successor = (hash(host), host)
        self.host_table[self.successor[0]] = self.successor[1]

    def lookup(self, key, n=replication):
        if n < 0:
            raise RuntimeError('Too many faulty processes.', 500)

        if key == self.id or DHTNode.between(self.predecessor[0], key, self.id):
            chain = []
        if key == self.successor[0] or DHTNode.between(self.id, key, self.successor[0]):
            url = address(self.successor[1])
            resp = requests.get(url)

            if resp.status_code != 200:
                return self.lookup(hash(key), n - 1)
            else:
                chain = [self.successor[1]]
        else:
            while True:
                id, host = min(
                    self.host_table.items(),
                    key=lambda x: DHTNode.distance(x[0], key)
                )

                url = address(host)
                resp = requests.get(url)

                if resp.status_code != 200:
                    if host == self.successor[1]:
                        return self.lookup(hash(key), n - 1)

                    del self.hash_table[id]
                else:
                    url = address(host) + 'lookup/{:d}/{:d}'.format(key, n)
                    resp = requests.get(url)

                    if resp.status_code != 200:
                        raise RuntimeError(resp.text, resp.status_code)

                    chain = [int(i) for i in resp.text.split('\n')]

                    break

        # Improve internal representation of the network
        for host in chain:
            if host is not None:
                self.host_table[hash(host)] = host

        return chain + [self.host]

    def exists(self, key):
        return hash(key) in self.hash_table

    def get(self, key):
        return self.hash_table.get(hash(key))

    def put(self, key, value):
        if self.exists(key):
            raise AttributeError
        else:
            self.hash_table[hash(key)] = value
