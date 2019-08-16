# DASH-Tools
 different tools for blockchain parsing and analyzing privateSend

Prerequisites

- python 3 with pymongo, requests, json
- MongoDB Server https://www.mongodb.com/download-center/community
- recommended: https://www.mongodb.com/download-center/compass (GUI to access DB)
    
Build the database

start the DASH daemon with the -rest argument, since we use the RESTful API to fetch blocks.
On Windows for ease of use create a startdaemon.bat in the dashcore-x.xx.x/bin folder:

    dashd.exe -printtoconsole=1 -rest -disablewallet=1
    
When the daemon is synced execute restfulparse.py with:

    python restfulparse.py
    
It creates the database 'blockchain' containing the collection 'blocks' at first use, or uses existing ones.
You can check this in the MongoDB compass. A full parse currently takes ~50GB of disk space. 

Building the database takes some time. You will notice it slows down. I was not able to identify the reason 
so when it gets too slow stop the process with 'Ctrl + C', restart your machine and start again.
The tool will check your last inserted block and start at its height with full speed again.

# Important

create a txid index in MongoDB, since we will use txids for all further DB queries. Use MongoDB 
compass, navigate to the 'blocks' collection, then 'Indexes' and then 'CREATE INDEX'.
Choose txid as name, and choose tx.txid as field.

When you are at a reasonable blockheight you can start to parse privateSends with the appropriate
blockheight, since it only goes backwards in the blockchain.

    python anonymityset.py
    
It asks for the transaction ID and will then yield results on the fly, while also offering 
the option to save all collected data in a JSON formatted file 'transactionID.txt' afterwards.
Please keep in mind a single parse, especially for privateSends with a high input count, will take some time.

# Notes

Currently this tool checks 8 rounds of mixing. Next versions will ask for desired mixing depth to check 
or use the maximum mixing rounds at a given height.

MongoDB is not the right database for this purpose, but it is pretty failsafe. Disadvantage: it's slow.
At a later stage I will release code for the Redis database, which is memory mapped and approximately 
20 times faster (tests show converting bytecode into python dictionaries slows this down. 
If you have a suggestion let me know).

A port to Redis is trivial, but it is not as failsafe.

The code is experimental. I do not guarantee it yields correct results. For a quick check use the dashradar.com 
graph.

This project is a learning project. I am a newb to github, so excuse 'newbish' github behaviour ;)

If you dig the code and find anything you'd like to comment please do so!