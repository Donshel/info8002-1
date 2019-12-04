# Distributed Fault-Tolerant Hash Table (DFTHT)

Project realized under the direction of [**Joeri Hermans**](https://github.com/JoeriHermans) as part of the course *Large scale data systems* given by [**Gilles Louppe**](https://github.com/glouppe) to graduate computer science students at the [University of Liège](https://www.uliege.be/) during the academic year 2019-2020.

## Altered Chord

The developed framework is an *altered* version of [Chord](https://en.wikipedia.org/wiki/Chord_(peer-to-peer)). It has been implemented using mainly [Flask](https://github.com/pallets/flask) and [Requests](https://github.com/psf/requests) Python libraries.

### Concept

As the regular Chord protocol, this version organizes the participating nodes in an *orverlay network*, where each node (machine) is responsible for a set of keys defined as `m`-bit identifiers. The overlay network is arranged in an *identifier circle* ranging from `0` to `2^m - 1`. The position (or identifier) `n` of a node on this circle is chosen by *hashing* the node IP address.

The responsibility  of a key `k` belongs to a node if it is the first node whose identifier `n` follows or equals `k` in the identifier circle. If true, `n` is said to be the *successor node* of `k` : `n = successor(k)`. The concept of successor is used for nodes as well : the successor of a node (whose identifier is `n`) is `m` such that `m = successor(n + 1)`. In this case, `n` is referenced as the *predecessor* of `m`.

Because, each key is under the responsibility of a node, the core usage of the Chord protocol is to query a key `k` from a client (a node as well), i.e. to find `successor(k)`. If the client is not the said successor, it will pass the query to another node **it knows**. This is called the *lookup* mechanism.

In the regular Chord protocol, each node keeps a *finger table* of up to `m` other (smartly selected) nodes which ensures *logarithmic* complexity for the lookup. However, this table has to be updated each time a node joins or leaves the network (or crashes) through a *stabilization* protocol running periodically in the background.

To avoid such processing waste, another mechanism has been implemented. Instead of returning `successor(k)`, the lookup function returns the *sequence* of nodes (their IP address) that were involved in the search and, thanks to its *recursive* implementation, the later can *improve* their internal representation of the network at the same time.

```python
def lookup(n, k):
    if n == successor(k):
        chain = []
    else:
        chain = lookup(next(n, k), k)
        improve(n, chain)

    return chain + [ip(n)]
```
> Pseudo-code (do not necessarily correspond to the reality).

The worst-case complexity of this procedure is `O(N)` where `N` is the number of nodes. But, assuming that the network isn't changing too quickly (several nodes joining between lookups), the average complexity will eventually be `O(1)` and no background process is required.

However, there is a tradeoff : the memory space needed to store the internal network representation is `O(N^2)` (`O(N)` for `N` nodes) instead of `O(N * log(N))` for the regular Chord protocol.

### Architecture

Each *node* is composed of two layers. The *external* layer (implemented by [`application.py`](python/application.py)) handles the incomming `HTTP` requests and transmit them to the *internal* layer which acts as a storage unit both for the files and the network representation.

### Requirements

```txt
certifi==2019.11.28
chardet==3.0.4
Click==7.0
Flask==1.1.1
idna==2.8
itsdangerous==1.1.0
Jinja2==2.10.3
MarkupSafe==1.1.1
requests==2.22.0
urllib3==1.25.7
Werkzeug==0.16.0
```

### Interface

In order to initialize a node, one shall call the following command
```bash
python python/application.py -p $PORT -b $BOOT
```
where `$PORT` is the port of the new node and `$BOOT` is the port of a node in a network. By default, both are set to `5000`. If `$PORT == $BOOT`, the node starts a new network.

> A node isn't activated until it receives its first request.

To communicate with the network, one can use the [curl](https://curl.haxx.se/) library.

### Interface

Among others, the framework presents the `exists`, `get`, `put` and `copy` requests (cf. [statement](statement.md)).

```bash
curl http://127.0.0.1:$PORT/exists/$PATH
curl http://127.0.0.1:$PORT/get/$PATH
curl http://127.0.0.1:$PORT/put/$PATH -X POST --data $VALUE --header 'Content-Type: application/json'
curl http://127.0.0.1:$PORT/copy/$SRC/$DST
```
> The parameter `--header 'Content-Type: application/json'` is mandatory.
