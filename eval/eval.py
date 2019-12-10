# Imports

import json
import matplotlib.pyplot as plt 
import numpy as np
import os

# Parameters

DIR = 'products/txt/'

# Read files

N = []
request = []
memory = []

for file in os.listdir(DIR):
    folder = DIR + file + '/'
    if os.path.isdir(folder):
        N.append(int(file))
        request.append([])
        memory.append([])

        with open(folder + 'lookup.txt', 'r') as f:
            for line in f.readlines():
                resp = len(json.loads(line))
                request[-1].append(resp)

        request[-1] = sum(request[-1]) / len(request[-1])

        with open(folder + 'network.txt', 'r') as f:
            for line in f.readlines():
                resp = len(json.loads(line))
                memory[-1].append(resp)

        memory[-1] = sum(memory[-1]) * N[-1] / len(memory[-1])

## Barplots

os.makedirs('products/png/', exist_ok=True)

plt.bar(N, request)
plt.xlabel('Number of nodes')
plt.ylabel('Requests per lookup')
plt.savefig('products/png/lookup.png', bbox_inches='tight')
plt.close()

plt.bar(N, memory)
plt.xlabel('Number of nodes')
plt.ylabel('Edges in the network')
plt.savefig('products/png/memory.png', bbox_inches='tight')
plt.close()
