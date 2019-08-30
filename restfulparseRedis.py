# Parses the DASH blockchain via the dashd Restful Api into an ultra fast memory mapped redis db
# start dashd.exe with -rest -disablewallet=1

# Copyright (C) 2019  Flenst

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.
import requests
import redis
import json

# initialize redis

db = redis.StrictRedis(host='127.0.0.1', port=6379, db=0)

global blockhash
global lastParsedBlockheight
global latestBlockheight

#  open file to read last inserted block or start from genesis
try:
    with open('lastparsedblockhash.txt', 'r') as f:
        blockhash = f.readline()
except:
    blockhash = '00000ffd590b1485b3caadc19b22e6379c733355108f107a430458cdf3407ab6'

def getheightbyhash(hash):
    global lastParsedBlockheight

    url = "http://127.0.0.1:9998/rest/block/" + hash + ".json"
    headers = {'Content-Type': 'application/json', 'Connection': 'close'}

    response = requests.get(url, headers=headers).json()
    return response['height']


def getmaxblockheight():
    global latestBlockheight

    url = "http://127.0.0.1:9998/rest/chaininfo.json"
    headers = {'Content-Type': 'application/json', 'Connection': 'close'}

    response = requests.get(url, headers=headers).json()
    latestBlockheight = response['blocks']


def getblockbyhash(hash):
    global blockhash

    url = "http://127.0.0.1:9998/rest/block/" + hash + ".json"
    headers = {'Content-Type': 'application/json', 'Connection':'close'}

    response = requests.get(url, headers=headers).json()
    blockhash = response['nextblockhash']

    #  pop unneccessary data to save storage space, could use an overhaul
    for e in ['size', 'version', 'type', 'locktime', 'instantlock']:
        response['tx'][0].pop(e)

    for i in response['tx']:
        if len(i['vin']) == 0:  # catch empty tx
            pass
        elif 'coinbase' in i['vin'][0]:  # catch coinbase tx
            for e in ['sequence']:
                i['vin'][0].pop(e)
            for e in ['valueSat']:
                 i['vout'][0].pop(e)
            for e in ['asm', 'hex', 'reqSigs', 'type']:
                i['vout'][0]['scriptPubKey'].pop(e)
        else:
             for e in ['size', 'version', 'type', 'locktime', 'instantlock']:  # catch all else
                 i.pop(e)
             for j in i['vout']:
                 for e in ['valueSat']:
                     j.pop(e)
                 for e in ['asm', 'hex', 'type']:  # no reqSigs since this broke parsing
                     j['scriptPubKey'].pop(e)
             for e in ['scriptSig', 'sequence']:
                 for j in i['vin']:
                     j.pop(e)

    for i in response['tx']:  # insert data into db
        db.set(i['txid'], json.dumps(i))

    if response['height'] % 1000 == 0:  # "progress bar" + save parsed blockhash into file
        with open('lastparsedblockhash.txt', 'w')as f:
            f.write(blockhash)
        print(response['height'])


lastParsedBlockheight = getheightbyhash(blockhash)
getmaxblockheight()
blocksToParse = latestBlockheight - lastParsedBlockheight
print('The database is', blocksToParse, 'blocks behind.')
print('Inserting blocks:')

for i in range(blocksToParse):
    getblockbyhash(blockhash)