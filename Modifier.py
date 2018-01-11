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


instagram_username = CredentialManager.get_value("InstagramUsername")
instagram_password = CredentialManager.get_value("InstagramPassword")

mongodb_username = CredentialManager.get_value("InstagramMongoDBUsername")
mongodb_password = CredentialManager.get_value("InstagramMongoDBPassword")
mongodb_ip_address = CredentialManager.get_value("InstagramMongoDBIPAddress")
mongodb_port = CredentialManager.get_value("InstagramMongoDBPort")

mongo_client_host = ("mongodb://{username}:{password}@{ip_address}:{port}/"
                        .format(username=mongodb_username, 
                                password=mongodb_password,
                                ip_address=mongodb_ip_address, 
                                port=mongodb_port))

print(mongo_client_host)
exit(0)

client = Instagram(instagram_username, instagram_password, mongo_client_host)

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



