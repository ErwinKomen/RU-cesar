"""
Extract POS tags by using Frog.
"""

import json

import sys
from pynlpl.clients.frogclient import FrogClient
port = 8020
frogclient = FrogClient('localhost', port, returnall=True)

import os
wordstream = ''
data_folder = '../data/output/1_preprocessed/'
for file in os.listdir(data_folder):
    path = os.path.join(data_folder, file)
    with open(path, 'rb') as reader:
        data = reader.read().decode('utf-8-sig')
        data = [line.split("\t")[-1] for line in data.split("\n")]
        wordstream += ' '.join(data)

window_size = 250
window_shift = 50
index = 0
with open('pos_tags.txt', 'w') as file:
    while index + window_size < len(wordstream):
        substream = wordstream[index:index + window_size]
        for data in frogclient.process(substream):
            sys.stdout.write('\r')
            percentage = round(100 * index / float(len(wordstream)), 2)
            sys.stdout.write(str(percentage) + '%')
            sys.stdout.flush()
            file.write(json.dumps(data) + "\n")
        index += window_shift