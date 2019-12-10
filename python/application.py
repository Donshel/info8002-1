# Imports
import json
import requests

from flask import Flask, request, jsonify
from dftht.dht import DHTNode, address, hash

# Parameters
replication = 3

# Application
app = Flask(__name__)

@app.before_first_request
def bootstrap():
    '''Bootstraps the internal node.'''
    global node
    node = DHTNode(request.host)

    if node.host != boot:
        # Join the network
        try:
            with node.lock:
                node.join(boot)
        except:
            shutdown()

@app.route('/shutdown')
def shutdown():
    '''Shutdowns the application.'''
    request.environ.get('werkzeug.server.shutdown')()
    return 'Server shutting down.\n'

@app.route('/')
def ping():
    '''Hello, World!'''
    return 'Hello, World!', 200

@app.route('/predecessor')
def predecessor():
    '''Returns the predecessor of the internal node.'''
    with node.lock:
        return jsonify(node.predecessor[1]), 200

@app.route('/network')
def network():
    '''Returns the node's internal representation of the network.'''
    with node.lock:
        return jsonify(node.host_table), 200

@app.route('/content')
def content():
    '''Returns all values stored within the node.'''
    with node.lock:
        return jsonify(node.hash_table), 200

@app.route('/update_predecessor/<host>')
def update_predecessor(host):
    '''Updates the predecessor of the internal node.'''
    try:
        with node.lock:
            node.update_predecessor(host)

        return 'Predecessor updated to {}.\n'.format(host), 200
    except Exception as e:
        return str(e), 500

@app.route('/lookup/<key>')
def lookup(key):
    '''Looks up the successor of a key.'''
    try:
        return jsonify(node.lookup(int(key))), 200
    except Exception as e:
        return str(e), 500

@app.route('/exists/<path>')
@app.route('/exists/<path>/<n>')
def exists(path, n=replication):
    '''Checks whether a value is stored at a path.'''
    n = min(int(n), replication)
    key = hash(path, replication - n + 1)

    try:
        assert n > 0, 'n should be strictly positive.'

        # Lookup successor of 'key'
        host = node.lookup(key)[0]

        if host == None:
            if n > 1:
                return exists(path, n - 1)
            else:
                raise KeyError('Unable to access path {}.'.format(path))
        elif host == node.host:
            # Request internal node
            with node.lock:
                return jsonify(node.exists(key, path)), 200
        else:
            # Request external node
            url = address(host) + 'exists/{}/{:d}'.format(path, n)
            resp = requests.get(url)

            return resp.text, resp.status_code
    except Exception as e:
            return str(e), 500

@app.route('/get/<path>')
@app.route('/get/<path>/<n>')
def get(path, n=replication):
    '''Returns the value stored at a path.'''
    n = min(int(n), replication)
    key = hash(path, replication - n + 1)

    try:
        assert n > 0, 'n should be strictly positive.'

        # Lookup successor of 'key'
        host = node.lookup(key)[0]

        if host == None:
            if n > 1:
                return get(path, n - 1)
            else:
                raise KeyError('Unable to access path {}.'.format(path))
        elif host == node.host:
            # Request internal node
            with node.lock:
                value = node.get(key, path)

            if value is None:
                return 'No value stored at path {}.\n'.format(path), 404

            return jsonify(value), 200
        else:
            # Request external node
            url = address(host) + 'get/{}/{:d}'.format(path, n)
            resp = requests.get(url)

            return resp.text, resp.status_code
    except Exception as e:
        return str(e), 500

@app.route('/put/<path>', methods=['POST', 'PUT'])
@app.route('/put/<path>/<n>', methods=['POST', 'PUT'])
def put(path, n=replication):
    '''Stores a value at a path.'''
    n = min(int(n), replication)
    key = hash(path, replication - n + 1)
    value = request.get_json()

    try:
        assert n > 0, 'n should be strictly positive.'

        # Lookup successor of 'key'
        host = node.lookup(key)[0]

        if host == None:
            if n > 1:
                # Start again with 'hash(path)'
                return put(path, n - 1)
            else:
                raise KeyError('Unable to access path {}.'.format(path))
        elif host == node.host:
            # Request internal node
            with node.lock:
                node.put(key, path, value)

            if n > 1:
                put(path, n - 1)

            return 'Value successfully stored at path {}.\n'.format(path), 200
        else:
            # Request external node
            url = address(host) + 'put/{}/{:d}'.format(path, n)
            resp = requests.post(url, json=value)

            return resp.text, resp.status_code
    except Exception as e:
        return str(e), 500

@app.route('/remove/<path>')
@app.route('/remove/<path>/<n>')
def remove(path, n=replication):
    '''Removes the value stored at a path.'''
    n = min(int(n), replication)
    key = hash(path, replication - n + 1)

    try:
        assert n > 0, 'n should be strictly positive.'

        # Lookup successor of 'key'
        host = node.lookup(key)[0]

        if host == None:
            if n > 1:
                return remove(path, n - 1)
            else:
                raise KeyError('Unable to access path {}.'.format(path))
        elif host == node.host:
            # Request internal node
            with node.lock:
                value = node.pop(key, path)

            if n > 1 and value is not None:
                remove(path, n - 1)

            return 'Value successfully removed from path {}.\n'.format(path), 200
        else:
            # Request external node
            url = address(host) + 'remove/{}/{:d}'.format(path, n)
            resp = requests.get(url)

            return resp.text, resp.status_code
    except Exception as e:
        return str(e), 500

@app.route('/copy/<src>/<dst>')
def copy(src, dst):
    '''Copies the value at a path to another.'''
    try:
        # Get value with path 'src'
        url = address(node.host) + 'get/{}'.format(src)
        resp = requests.get(url)

        if resp.status_code != 200:
            return resp.text, resp.status_code

        # Put value with path 'dst'
        url = address(node.host) + 'put/{}'.format(dst)
        resp = requests.post(url, json=json.loads(resp.text))

        return resp.text, resp.status_code
    except Exception as e:
        return str(e), 500

@app.route('/delete/<a>/<b>')
def delete(a, b):
    '''Deletes all values stored within an interval in the internal node.'''
    try:
        with node.lock:
            node.delete(int(a), int(b))

        return 'Content successfully deleted.\n', 200
    except Exception as e:
        return str(e), 500

@app.route('/list')
def ls():
    '''Lists all occupied paths within the network.'''
    paths = {j[0] for i in node.hash_table.values() for j in i}
    visited = {node.id}
    stack = list(node.host_table.items())

    # Depth-first search
    while stack:
        id, host = stack.pop()
        id = int(id)

        if id in visited:
            # If already visited
            continue

        # Add to visited
        visited.add(id)

        try:
            # Extend stack
            url = address(host) + 'network'
            resp = requests.get(url)

            if resp.status_code != 200:
                raise ConnectionError

            stack.extend(json.loads(resp.text).items())

            # Gather content
            url = address(host) + 'content'
            resp = requests.get(url)

            if resp.status_code != 200:
                raise ConnectionError

            paths.update(j[0] for i in json.loads(resp.text).values() for j in i)
        except:
            pass

    return jsonify(sorted(paths)), 200

# Main
if __name__ == '__main__':
    from argparse import ArgumentParser

    parser = ArgumentParser()

    parser.add_argument('-p', '--port', type=int, default=5000)
    parser.add_argument('-b', '--boot', type=str, default='127.0.0.1:5000')

    args = parser.parse_args()

    port = args.port
    boot = args.boot

    app.run(port=port)
