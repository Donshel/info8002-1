# Imports
import json
import requests

from hashlib import sha1
from threading import Lock

# Parameters
size = 2 ** 10

# Methods
def address(host):
    return 'http://127.0.0.1:{:d}/'.format(host)

def contact(url, msg='', timeout=0.1):
    try:
        resp = requests.get(url, timeout=timeout)

        if resp.status_code != 200:
            raise ConnectionError

        return resp.text
    except:
        raise ConnectionError(msg)

def hash(x):
    return int(int.from_bytes(sha1(str(x).encode()).digest(), 'big') % size)

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
        return (a == c) or (b != a and DHTNode.distance(a, b) + DHTNode.distance(b, c) == DHTNode.distance(a, c))

    # Class methods
    def __init__(self, host):
        self.host = host
        self.id = hash(self.host)

        self.predecessor = (self.id, self.host)
        self.successor = (self.id, self.host)

        self.host_table = {}
        self.hash_table = {}

        self.lock = Lock()

    def join(self, boot):
        # Ping boot
        url = address(boot)
        contact(url)

        # Lookup successor
        url = address(boot) + 'lookup/{:d}'.format(self.id)
        resp = contact(url)
        successor = json.loads(resp)[0]

        # Search predecessor
        url = address(successor) + 'predecessor'
        resp = contact(url)
        predecessor = json.loads(resp)

        # Update successor and predecessor
        self.update_predecessor(predecessor)
        self.update_successor(successor)

        # Inform predecessor
        url = address(predecessor) + 'update_successor/{:d}'.format(self.host)
        contact(url)

        # Inform successor
        try:
            url = address(successor) + 'update_predecessor/{:d}'.format(self.host)
            contact(url)
        except:
            # Revert predecessor
            url = address(predecessor) + 'update_successor/{:d}'.format(successor)
            contact(url)

        # Take space domain responsibility
        url = address(successor) + 'content/{:d}/{:d}'.format(hash(predecessor), self.id)
        resp = contact(url)

        content = json.loads(resp)
        for key, values in content.items():
            self.hash_table[int(key)] = values

        try:
            url = address(successor) + 'delete/{:d}/{:d}'.format(hash(predecessor), self.id)
            contact(url)
        except:
            pass

    def update_predecessor(self, host):
        self.predecessor = (hash(host), host)
        self.host_table[self.predecessor[0]] = self.predecessor[1]

    def update_successor(self, host):
        self.successor = (hash(host), host)
        self.host_table[self.successor[0]] = self.successor[1]

    def lookup(self, key):
        if DHTNode.between(self.predecessor[0], key, self.id):
            chain = []
        elif DHTNode.between(self.id, key, self.successor[0]):
            try:
                url = address(self.successor[1])
                resp = contact(url)

                chain = [self.successor[1]]
            except:
                chain = [None]
        else:
            while True:
                id, host = min(
                    self.host_table.items(),
                    key=lambda x: DHTNode.distance(x[0], key)
                )

                try:
                    url = address(host) + 'lookup/{:d}'.format(key)
                    resp = contact(url)

                    chain = json.loads(resp)
                except:
                    if host == self.successor[1]:
                        chain = [None]
                    else:
                        del self.host_table[id]
                        continue

                break

        # Improve internal representation of the network
        for host in chain:
            if host is not None:
                self.host_table[hash(host)] = host

        return chain + [self.host]

    def exists(self, path):
        return self.get(path) is not None

    def get(self, path):
        path = str(path)
        key = hash(path)

        try:
            return next(i[1] for i in self.hash_table[key] if i[0] == path)
        except:
            return None

    def put(self, path, value):
        path = str(path)
        key = hash(path)

        if key in self.hash_table:
            if self.exists(path):
                raise KeyError('Value already stored with path {}.'.format(path))
            else:
                self.hash_table[key].append((path, value))
        else:
            self.hash_table[key] = [(path, value)]

    def content(self, a, b):
        return dict([i for i in self.hash_table.items() if DHTNode.between(a, i[0], b)])

    def delete(self, a, b):
        self.hash_table = dict(
            [i for i in self.hash_table.items() if not DHTNode.between(a, i[0], b)]
        )
