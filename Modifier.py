#!/usr/bin/env python

import json
import random
import subprocess
import time

from bson import json_util
from CredentialManager import CredentialManager
from pymongo import MongoClient
from InstagramAPI import InstagramAPI
from Instagram import Instagram
from Users import InstagramUser

import pymongo
import requests


credentials = CredentialManager()

insta_user, insta_pass = credentials.get_account('Instagram')
mongo_user, mongo_pass = credentials.get_account('InstagramMongoDB')
mongo_ip, mongo_port = credentials.get_values('InstagramMongoDBIPAddress', 'InstagramMongoDBPort')


mongo_client_host = ("mongodb://{username}:{password}@{ip_address}:{port}/"
                        .format(username=mongo_user, 
                                password=mongo_pass,
                                ip_address=mongo_ip, 
                                port=mongo_port))

print(mongo_client_host)
exit(0)

client = Instagram(insta_user, insta_pass, mongo_client_host)

api = None
database = None
users_collection = None
database_client = MongoClient(mongo_client_host)
database = database_client["Instagram"]
users_collection = database["users"]

client.following_follower_diff()

#Add the most recent followers to the database
"""client.IS_DEVELOPMENT = False
client.add_followers_to_db(skip_saved=True)
"""

#users_collection.update_many({}, { '$set': {'is_follower': True}})



