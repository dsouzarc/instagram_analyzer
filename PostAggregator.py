#!/usr/bin/env python
"""PostAggregator.py: Handles getting newsfeed and storing post information to Mongo"""

import json
import random
import subprocess
import sys
import time

from bson import json_util
from CredentialManager import CredentialManager
from InstagramAPI import InstagramAPI
from Instagram import Instagram
from pymongo import MongoClient
from Users import InstagramUser

import pymongo
import requests


class PostAggregator(object):

    _instagram = None #Instagram wrapper
    _database = None
    
    def __init__(self, instagram):
        """ Constructor

        Args:
            instagram (`obj`: Instagram): Instagram object from Instagram.py
        """

        self._instagram = instagram
        self._database = instagram._database


    def store_posts_for_user(self, username_id, table_name, max_posts=sys.maxint):
        """Gets the posts for a user and stores them in MongoDB

        Args:
            username_id (int): The user's ID
            table_name (str): String for the table name in Mongo
            max_posts (int): Maximum number of posts to store
        """

        counter = 0
        total_posts = list()
        mongo_table = self._database[table_name]

        userfeed_generator = aggregator._instagram.user_feed_generator(username_id, 
                                                                       max_pages=max_posts)

        for posts_list in userfeed_generator:
            for post in posts_list:
                mongo_table.insert_one(post)
                total_posts.append(post)
            counter += 1
            print("# of posts: %s\t # of API requests: %s" % (len(total_posts), counter))

            if counter % 4 == 0:
                time.sleep(random.randint(random.randint(20, 110), random.randint(111, 180)))
            else:
                time.sleep(random.randint(random.randint(10, 30), random.randint(31, 45)))



if __name__ == "__main__":

    client = Instagram.default_client()
    aggregator = PostAggregator(client)

    aggregator.store_posts_for_user(1405454497, 'tfm_girls_2', 5)
