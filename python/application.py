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
    global node

    node = DHTNode(port)

    if port != boot:
        try:
            with node.lock:
                node.join(boot)
        except:
            shutdown()

@app.route('/shutdown')
def shutdown():
    request.environ.get('werkzeug.server.shutdown')()
    return 'Server shutting down.'

@app.route('/')
def ping():
    return 'Hello, World!', 200

@app.route('/state')
def state():
    state = {
        'host': node.host,
        'id': node.id,
        'predecessor': node.predecessor,
        'successor': node.successor,
        'host_table': node.host_table,
        'hash_table': node.hash_table
    }

    return jsonify(state), 200

@app.route('/predecessor')
def predecessor():
    return jsonify(node.predecessor[1]), 200

@app.route('/update_predecessor/<host>')
def update_predecessor(host):
    try:
        with node.lock:
            node.update_predecessor(int(host))

        return 'Predecessor updated to {}.'.format(host), 200
    except Exception as e:
        return str(e), 500

@app.route('/update_successor/<host>')
def update_successor(host):
    try:
        with node.lock:
            node.update_successor(int(host))

        return 'Successor updated to {}.'.format(host), 200
    except Exception as e:
        return str(e), 500

@app.route('/lookup/<key>')
def lookup(key):
    try:
        return jsonify(node.lookup(int(key))), 200
    except Exception as e:
        return str(e), 500

@app.route('/exists/<path>')
@app.route('/exists/<path>/<n>')
def exists(path, n=replication):
    path = str(path)
    key = hash(path)
    n = int(n)

    try:
        assert n > 0, 'n should be strictly positive.'

        host = node.lookup(key)[0]

        if host == None:
            if n > 1:
                return exists(key, n - 1)
            else:
                raise KeyError('Unable to access path {}.'.format(path))
        elif host == node.host:
            with node.lock:
                return jsonify(node.exists(path)), 200
        else:
            url = address(host) + 'exists/{}/{:d}'.format(path, n)
            resp = requests.get(url)

            return resp.text, resp.status_code
    except Exception as e:
            return str(e), 500

@app.route('/get/<path>')
@app.route('/get/<path>/<n>')
def get(path, n=replication):
    path = str(path)
    key = hash(path)
    n = int(n)

    try:
        assert n > 0, 'n should be strictly positive.'

        host = node.lookup(key)[0]

        if host == None:
            if n > 1:
                return get(key, n - 1)
            else:
                raise KeyError('Unable to access path {}.'.format(path))
        if host == node.host:
            with node.lock:
                value = node.get(path)

            if value is None:
                return 'No value stored with path {}.'.format(path), 404

            return jsonify(value), 200
        else:
            url = address(host) + 'get/{}/{:d}'.format(path, n)
            resp = requests.get(url)

            return resp.text, resp.status_code
    except Exception as e:
        return str(e), 500

@app.route('/put/<path>', methods=['POST', 'PUT'])
@app.route('/put/<path>/<n>', methods=['POST', 'PUT'])
def put(path, n=replication):
    path = str(path)
    key = hash(path)
    value = request.get_json()
    n = int(n)

    try:
        assert n > 0, 'n should be strictly positive.'

        host = node.lookup(key)[0]

        if host == None:
            if n > 1:
                return put(key, n - 1)
            else:
                raise KeyError('Unable to access path {}.'.format(path))
        if host == node.host:
            with node.lock:
                node.put(path, value)

            if n > 1:
                put(key, n - 1)

            return 'Value successfully stored with path {}.'.format(path), 200
        else:
            url = address(host) + 'put/{}/{:d}'.format(path, n)
            resp = requests.post(url, json=value)

            return resp.text, resp.status_code
    except Exception as e:
        return str(e), 500

@app.route('/copy/<src>/<dst>')
def copy(src, dst):
    try:
        url = address(node.host) + 'get/{}'.format(src)
        resp = requests.get(url)

        if resp.status_code != 200:
            return resp.text, resp.status_code

        url = address(node.host) + 'put/{}'.format(dst)
        resp = requests.post(url, json=json.loads(resp.text))

        return resp.text, resp.status_code
    except Exception as e:
        return str(e), 500

@app.route('/content/<a>/<b>')
def content(a, b):
    try:
        with node.lock:
            return jsonify(node.content(int(a), int(b))), 200
    except Exception as e:
        return str(e), 500

@app.route('/delete/<a>/<b>')
def delete(a, b):
    try:
        with node.lock:
            node.delete(int(a), int(b))

        return 'Content successfully deleted.', 200
    except Exception as e:
        return str(e), 500

if __name__ == '__main__':
    from argparse import ArgumentParser

    parser = ArgumentParser()

    parser.add_argument('-p', '--port', type=int, default=5000)
    parser.add_argument('-b', '--boot', type=int, default=5000)

    args = parser.parse_args()

    port = args.port
    boot = args.boot

    app.run(port=port)
