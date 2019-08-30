# yields your anonymity set after given rounds of mixing (you hide between x possible originating addresses).
# offers the possibility to export all data in JSON format.
#
# Copyright (C) 2019  Flenst
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# # This program is distributed in the hope that it will be useful,
# # but WITHOUT ANY WARRANTY; without even the implied warranty of
# # MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# # GNU General Public License for more details.
#
# # You should have received a copy of the GNU General Public License
# # along with this program. If not, see <https://www.gnu.org/licenses/>.
import redis
import time
import ujson
from collections import Counter

def main():

#initialize needed variables
    global db
    db = redis.StrictRedis(host='127.0.0.1', port=6379, db=0, decode_responses=True)
    global querycounter
    global mixing_rounds
    global denominations

    privatesendtxid = input('Which privateSend transactionID do you want to check?: ')

    desired_depth = int(input('How many mixing rounds to check?: '))
    # build dictionaries to store parsing data
    mixing_rounds = {i + 1: [] for i in range(desired_depth)}
    denominations = {i + 1: [] for i in range(desired_depth)}
    addresses = {i + 1: [] for i in range(desired_depth)}
    anonymity_set = []
    querycounter = 0

    start = time.time()

    # generate round 1 of mixing tx, while preventing duplicates
    for i in gettx(privatesendtxid)['vin']:
        if i['txid'] not in mixing_rounds[1] and len(gettx(i['txid'])['vin']) == len(gettx(i['txid'])['vout']):
            mixing_rounds[1].append(i['txid'])
    print('Unique mixing transactions in round 1 :', (len(mixing_rounds[1])))

    # Fetch mixing rounds and denomination tx
    for i in range(2, desired_depth+1):
        checkinputs(i)

    print('Fetching last rounds denomination inputs...')
    # Fetch denomination tx in last round
    for i in mixing_rounds[desired_depth]:
        for j in gettx(i)['vin']:
            localquery = gettx(j['txid'])
            if len(localquery['vin']) != len(localquery['vout']):
                if j['txid'] == None:
                    print('Found None!')
                denominations[desired_depth].append(j['txid'])


    for key, val in denominations.items():
        print('Denomination inputs in round', key, ':', len(denominations[key]))

    for key, val in denominations.items():
        for j in val:
            txid = gettx(j)
            if len(txid['vin']) == 0:  # catch empty tx
                pass
            elif 'coinbase' in txid['vin'][0]:
                pass
            else:
                vout = txid['vin'][0]['vout']
                txid_2 = gettx(txid['vin'][0]['txid'])
                try:
                    for i in txid_2['vout']:
                        if i['n'] == vout:
                            addresses[key].append(i['scriptPubKey']['addresses'][0])
                except:
                    print(txid)

    for key, val in addresses.items():
        if len(val) > 0:
            print("Addresses occuring in round", key, Counter(val).most_common(250))

    for key, val in addresses.items():
        anonymity_set.extend(val)
    anonymity_set = set(anonymity_set)

    print('Total anonymity set (unique possible originating addresses):', len(anonymity_set))

    print("# of inputs in this privateSend: ", len(gettx(privatesendtxid)['vin']))

    finish = time.time()
    print('This parse took:', finish - start, 'seconds.')
    print("Database was queried ", querycounter, "times.")

    # create optional export data dictionary, dump as JSON file as txid.txt
    export = input('Export JSON to file? [y/n]: ')
    if export == 'yes' or export == 'y':
        data = {'transactionID': privatesendtxid,
                'anonymitySet': len(anonymity_set),
                'mixing_rounds': [{i + 1: {'mixing_tx': mixing_rounds[i+1],
                                           'denomination_tx': list(set(denominations[i+1])),
                                           'addresses': addresses[i+1]} for i in range(desired_depth)}]}
        with open('%s.txt' % privatesendtxid, 'w') as json_file:
            ujson.dump(data, json_file)


def gettx(txid):

    try:
        global querycounter
        querycounter = querycounter + 1
        query = ujson.loads(db.get(txid))

        return query
    except:
        print(db.get(txid))


def checkinputs(depth):
    # pipelining db queries, significant speedup, but messier code
    # I am very sure this can be cleaned up or be more efficient
    pipe = db.pipeline()
    piped = []
    piped_dict = {}
    global querycounter
    counter = 0
    next_round = []
    next_round_piped = []
    next_round_piped_dict = {}

    for i in mixing_rounds[depth-1]:  # generate string-list through redis pipe
        pipe.get(i)
        counter += 1
        querycounter += 1
        if counter % 500 == 0:
            responses = pipe.execute()
            counter = 0
            for response in responses:
                piped.append(response)
    responses = pipe.execute()
    for response in responses:
        piped.append(response)

    for i in piped:  # generate JSON dictionary
        tempjson = ujson.loads(i)
        piped_dict[tempjson['txid']] = tempjson

    for key in piped_dict:
        for i in piped_dict[key]['vin']:
            next_round.append(i['txid'])

    for i in next_round:  # generate string-list through redis pipe for next round
        pipe.get(i)
        counter += 1
        querycounter += 1
        if counter % 500 == 0:
            responses = pipe.execute()
            counter = 0
            for response in responses:
                next_round_piped.append(response)
    responses = pipe.execute()
    for response in responses:
        next_round_piped.append(response)

    for i in next_round_piped:  # generate JSON dictionary
        tempjson = ujson.loads(i)
        next_round_piped_dict[tempjson['txid']] = tempjson

    for key in next_round_piped_dict:  # check if mixing round or denomination transaction
        if len(next_round_piped_dict[key]['vin']) == len(next_round_piped_dict[key]['vout']):
            mixing_rounds[depth].append(key)
        if len(next_round_piped_dict[key]['vin']) != len(next_round_piped_dict[key]['vout']):
            denominations[depth - 1].append(key)
    mixing_rounds[depth] = list(set(mixing_rounds[depth]))
    print('Unique mixing transactions in round', depth, ': ' + str(len(mixing_rounds[depth])))


def createdict(string):
    tempjson = ujson.loads(string)
    dictitem = tempjson
    return dictitem


if __name__ == "__main__":
    main()
