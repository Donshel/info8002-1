from flask import Flask, request

import requests

from dht import DHTNode, replication, address

# Application
app = Flask(__name__)

@app.before_first_request
def bootstrap():
    global node

    # Initialize node
    node = DHTNode(port)

    # Join the bootstrap node
    if port != boot:
        node.join(boot)

@app.route('/')
def ping():
    state = {
        'host': str(node.host),
        'id': str(node.id),
        'predecessor': str(node.predecessor),
        'successor': str(node.successor),
        'host_table': '\n'.join([str(value) for key, value in node.host_table.items()])
    }

    return state, 200

@app.route('/predecessor')
def predecessor():
    return str(node.predecessor[1]), 200

@app.route('/update_predecessor/<host>')
def update_predecessor(host:int):
    host = int(host)

    try:
        node.update_predecessor(host)
        return 'Predecessor updated to {:d}'.format(host), 200
    except:
        return 'Unexpected runtime error.', 500

@app.route('/update_successor/<host>')
def update_successor(host:int):
    host = int(host)

    try:
        node.update_successor(host)
        return 'Successor updated to {:d}'.format(host), 200
    except:
        return 'Unexpected runtime error.', 500

@app.route('/lookup/<key>/<n>')
def lookup(key:int, n:int):
    key, n = int(key), int(n)

    try:
        return '\n'.join([str(i) for i in node.lookup(key, n)]), 200
    except:
        return 'Unexpected runtime error.', 500

@app.route('/exists/<key>')
def exists(key):
    host = node.lookup(hash(key))[0]

    if host == node.host:
        return str(node.exists(key)), 200
    else:
        url = address(host) + 'exists/{}'.format(key)
        resp = requests.get(url)
        return resp.text, resp.status_code

@app.route('/get/<key>')
def get(key):
    host = node.lookup(hash(key))[0]

    if host == node.host:
        value = node.get(key)

        if value is None:
            return 'Not Found.', 404
        else:
            return str(value), 200
    else:
        url = address(host) + 'get/{}'.format(key)
        resp = requests.get(url)
        return resp.text, resp.status_code

@app.route('/put', methods=['POST', 'PUT'])
def put():
    data = request.get_json()
    key = data['key']
    value = data['value']

    host = node.lookup(hash(key))[0]

    if host == node.host:
        try:
            node.put(key, value)
            return 'Value stored.', 200
        except:
            return 'Already exists.', 403
    else:
        url = address(host) + 'put'
        resp = requests.post(url, json={'key': key, 'value': value})
        return resp.text, resp.status_code

@app.route('/fake/<key>')
def fake(key):
    url = address(node.host) + 'put'
    resp = requests.post(url, json={'key': key, 'value': hash(key)})
    return resp.text, resp.status_code

if __name__ == '__main__':
    from argparse import ArgumentParser

    parser = ArgumentParser()

    parser.add_argument('-p', '--port', type=int, default=5000)
    parser.add_argument('-b', '--boot', type=int, default=5000)

    args = parser.parse_args()

    port = args.port
    boot = args.boot

    app.run(debug=True, port=port)
