# Parses the DASH blockchain via the dashd Restful Api into a faster mongodb
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
import pymongo


def main():
    global mydb
    global myclient
    global mycol

    myclient = pymongo.MongoClient("mongodb://127.0.0.1:27017")
    mydb = myclient["blockchain"]

    mycol = mydb["blocks"]

    # insert genesis block if needed
    if mycol.count() == 0:
        getblockbyhash('00000ffd590b1485b3caadc19b22e6379c733355108f107a430458cdf3407ab6')

    lastParsedBlock = mycol.find().sort([( '$natural', -1 )]).limit(1)

    global blockhash
    global latestBlockheight
    blockhash = lastParsedBlock[0]['nextblockhash']
    lastParsedBlockheight = lastParsedBlock[0]['height']

    getMaxBlockheight()
    blocksToParse = latestBlockheight - lastParsedBlockheight
    print('The database is', blocksToParse, 'blocks behind.')
    print('Inserting blocks:')

    printProgressBar(0, blocksToParse, prefix='Progress:', suffix='Complete', length=50)
    for i in range(blocksToParse):
        getblockbyhash(blockhash)
        # Update Progress Bar
        printProgressBar(i + 1, blocksToParse, prefix='Progress:', suffix='Complete', length=50)

def getMaxBlockheight():
    global latestBlockheight

    url = "http://127.0.0.1:9998/rest/chaininfo.json"
    headers = {'Content-Type': 'application/json', 'Connection': 'close'}

    response = requests.get(url, headers=headers).json()
    latestBlockheight = response['blocks']

def getblockbyhash(hash):
    global blockhash
    global mycol

    url = "http://127.0.0.1:9998/rest/block/" + hash + ".json"
    headers = {'Content-Type': 'application/json', 'Connection':'close'}

    # Example echo method
    payload = {
    }
    response = requests.get(url, headers=headers).json()
    blockhash = response['nextblockhash']

    mycol.insert_one(response)

# Print iterations progress, copy-paste from https://stackoverflow.com/a/34325723
def printProgressBar (iteration, total, prefix = '', suffix = '', decimals = 3, length = 100, fill = '█'):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
    """
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    print('\r%s |%s| %s%% %s' % (prefix, bar, percent, suffix), end = '\r')
    # Print New Line on Complete
    if iteration == total:
        print()

if __name__ == "__main__":
    main()












