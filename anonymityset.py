# yields your anonymity set after 8 rounds of mixing (you hide between x possible originating addresses).
# offers the possibility to export all data in JSON format.

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
import pymongo
import json


def main():

    # initialize needed variables/connect to MongoDB
    global mydb
    global myclient
    global mycol

    myclient = pymongo.MongoClient("mongodb://127.0.0.1:27017")
    mydb = myclient["blockchain"]
    mycol = mydb["blocks"]

    global mixing_rounds
    global denominations

    privatesendtxid = input('Which privateSend transactionID do you want to check?: ')
    mixing_rounds = {1: [], 2: [], 3: [], 4: [], 5: [], 6: [], 7: [], 8: []}
    denominations = {1: [], 2: [], 3: [], 4: [], 5: [], 6: [], 7: [], 8: []}
    addresses = {1: [], 2: [], 3: [], 4: [], 5: [], 6: [], 7: [], 8: []}
    anonymity_set = []

    # generate round 1 of mixing tx, while preventing duplicates
    for i in gettx(privatesendtxid)[0]['vin']:
        if i['txid'] not in mixing_rounds[1] and len(gettx(i['txid'])[0]['vin']) == len(gettx(i['txid'])[0]['vout']):
            mixing_rounds[1].append(i['txid'])
    print('Unique mixing transactions in round 1 :', (len(mixing_rounds[1])))

    # Fetch mixing rounds and denomination tx
    for i in range(2, 9):
        checktx(i)

    print('Fetching denomination inputs:')
    # Fetch denomination tx in last round
    for txid in mixing_rounds[8]:
        for i in gettx(txid)[0]['vin']:
            localquery = gettx(i['txid'])
            if len(localquery[0]['vin']) != len(localquery[0]['vout']):
                denominations[8].append(i['txid'])

    for key, val in denominations.items():
        print('Denomination transactions in round', key, ':', len(denominations[key]))

    print('Fetching possible originating addresses:')

    for key, val in denominations.items():
        for j in val:
            txid = gettx(j)
            if 'coinbase' in txid[0]['vin'][0]:
                pass
            else:
                vout = txid[0]['vin'][0]['vout']
                txid_2 = gettx(txid[0]['vin'][0]['txid'])
                for i in txid_2[0]['vout']:
                    if i['n'] == vout:
                        addresses[key].append(i['scriptPubKey']['addresses'][0])

    for key, val in addresses.items():
        addresses[key] = list(set(val))

    print('Unique addresses per round:')

    for key, val in addresses.items():
        print(key, ':', len(val))

    for key, val in addresses.items():
        anonymity_set.extend(val)
    print(len(anonymity_set))
    anonymity_set = set(anonymity_set)

    print('Total anonymity set:', len(anonymity_set))

    export = input('Export JSON to file? [y/n]:')
    if export == 'yes' or export == 'y':
        data = {'transactionID': privatesendtxid,
                'anonymitySet': len(anonymity_set),
                'mixing_rounds': [{1: {'mixing_tx': mixing_rounds[1],
                                       'denomination_tx': list(set(denominations[1])),
                                       'addresses': addresses[1]}},
                                  {2: {'mixing_tx': mixing_rounds[2],
                                       'denomination_tx': list(set(denominations[2])),
                                       'addresses': addresses[2]}},
                                  {3: {'mixing_tx': mixing_rounds[3],
                                       'denomination_tx': list(set(denominations[3])),
                                       'addresses': addresses[3]}},
                                  {4: {'mixing_tx': mixing_rounds[4],
                                       'denomination_tx': list(set(denominations[4])),
                                       'addresses': addresses[4]}},
                                  {5: {'mixing_tx': mixing_rounds[5],
                                       'denomination_tx': list(set(denominations[5])),
                                       'addresses': addresses[5]}},
                                  {6: {'mixing_tx': mixing_rounds[6],
                                       'denomination_tx': list(set(denominations[6])),
                                       'addresses': addresses[6]}},
                                  {7: {'mixing_tx': mixing_rounds[7],
                                       'denomination_tx': list(set(denominations[7])),
                                       'addresses': addresses[7]}},
                                  {8: {'mixing_tx': mixing_rounds[8],
                                       'denomination_tx': list(set(denominations[8])),
                                       'addresses': addresses[8]}}]}
        with open('%s.txt' % privatesendtxid, 'w') as json_file:
            json.dump(data, json_file)


def checktx(mixinground):

    # get previous mixing rounds and find denominations
    for i in mixing_rounds[mixinground - 1]:
        for j in gettx(i)[0]['vin']:
            localtxid = gettx(j['txid'])
            if len(localtxid[0]['vin']) == len(localtxid[0]['vout']):
                mixing_rounds[mixinground].append(j['txid'])
            if len(localtxid[0]['vin']) != len(localtxid[0]['vout']):
                denominations[mixinground - 1].append(j['txid'])
    mixing_rounds[mixinground] = list(set(mixing_rounds[mixinground]))
    print('Unique mixing transactions in round', mixinground, ': ' + str(len(mixing_rounds[mixinground])))


def gettx(txid):

    query = mycol.find({'tx.txid': txid}, {'_id': 0})
    return [item for item in query[0]['tx'] if item.get('txid') == txid]


if __name__ == "__main__":
    main()
