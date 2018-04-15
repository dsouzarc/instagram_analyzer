#!/usr/bin/env python
"""InstagramAnalyzer.py: Interacts with Instagram.py and MongoDB for analysis"""

import inspect
import json
import os
import random
import subprocess
import sys
import time

from bson import json_util
from CredentialManager import CredentialManager
from Instagram import Instagram
from InstagramAPI import InstagramAPI
from pymongo import MongoClient
from Users import InstagramUser

import pymongo
import requests


####################################################################
#                   Written by Ryan D'souza
#           Main class for analyzing and storing Instagram Data
####################################################################




class InstagramAnalyzer(Instagram):
    """Main class that analyzes Instagram and stores the data in MongoDB"""

    IS_DEVELOPMENT = True

    _database = None
    _users_collection = None


    def __init__(self, insta_username, insta_password, mongoclient_host, save_file_path=None):
        """Constructor

        Args:
            insta_username (str): string version of the username i.e.: 'dsouzarc'
            insta_password (str): string version of the password
            mongoclient_host (str): string host for MongoDB instance i.e.: "localhost://27017"
        """


        Instagram.__init__(self, insta_username=insta_username, 
                            insta_password=insta_password, 
                            save_file_path=save_file_path)

        database_client = MongoClient(mongoclient_host)
        self._database = database_client["Instagram"]
        self._users_collection = self._database["users"]

        self._users_collection.create_index("pk", unique=True)


    #Convenience method
    def get_following(self, from_mongo=True, from_file=False):
        """Gets a list of all the users we are following on Instagram.

        Args:
            from_mongo (bool): bool for whether we should get saved Mongo data or live data
            from_file (bool): bool for whether we should get the data from a saved file

        Returns:
            dict(pk, dict): dict of who we are following. key: user PK, value: user
        """

        all_following = dict()
        following = list()

        #Get the data from Mongo
        if from_mongo:
            following = self._users_collection.find({'am_following': True})

        #Get the live data
        elif not from_mongo and not from_file:
            following = self.getTotalSelfFollowers()
            json.dump(following, open('all_following.json', 'w'), indent=4)

        #Get the data from a saved file
        else:
            saved_following = json.load(open('all_following.json', 'r'))

        for saved_following in following:
            saved_following['am_following'] = True
            all_following[saved_following['pk']] = saved_following

        return all_following


    #Convenience method
    def get_followers(self, from_mongo=True, from_file=False):
        """Gets a list of all the users that follow us on Instagram

        Args:
            from_mongo (bool): bool for whether we should get saved Mongo data or live data
            from_file (bool): bool for whether we should get the data from a saved file

        Returns:
            dict(pk, dict): dict of who follows us. key: user PK, value: user
        """

        all_followers = dict()
        followers = list()

        #Get the data from Mongo
        if from_mongo:
            followers = self._users_collection.find({'is_follower': True})

        #Get the live data
        elif not from_mongo and not from_file:
            followers = self.getTotalSelfFollowers()
            json.dump(followers, open('all_followers.json', 'w'), indent=4)

        #Get the data from a saved file
        else:
            followers = json.load(open('all_followers.json', 'r'))

        for follower in followers:
            follower['is_follower'] = True
            all_followers[follower['pk']] = follower

        return all_followers


    #For adding user information to Mongo
    def add_users_to_db(self, user_pks, skip_saved=True, is_follower=False, am_following=False):
        """Given a list of users, for each user, gets their information (1 API call)
            and saves it to MongoDB

        Args:
            user_pks (list(int)): list(int) of users' PKs
            skip_saved (bool): bool indicating if we should replace the data if it is in Mongo
            is_follower (bool): bool indicating if the user follows us
            am_following (bool): bool indicating if we follow the user
        """

        skip_user_pks = set()

        #Add the saved user PKs from MongoDB to the Set
        if skip_saved:
            saved_user_pks = self._users_collection.find({}, {'pk': 1, '_id': 0})
            for saved_user_pk in saved_user_pks:
                skip_user_pks.add(saved_user_pk['pk'])


        for user_pk in user_pks:
            if user_pk in skip_user_pks:
                print("Skipping: " + str(user_pk))
                continue

            #New user, get their information
            try:
                raw_user_result = self.getUsernameInfo(user_pk)
                raw_user = self.LastJson["user"]

            #Error getting user from Instagram API - sleep then try again
            except requests.exceptions.RequestException as e:
                print("Requests exception: %s" % (e))
                all_followers.append(follower)
                time.sleep(random.randint(180, 10 * 180))

            #No error - let's insert the user into Mongo
            else:
                user = InstagramUser(raw_user, 
                                     is_follower=is_follower, 
                                     am_following=am_following)
                user.add_update("inserted")

                try:
                    inserted_result = self._users_collection.insert_one(user.storage_dict())

                #User already exists in MongoDB - let's replace
                except pymongo.errors.DuplicateKeyError:
                    self._users_collection.delete_one({"pk": user.pk})
                    inserted_result = self._users_collection.insert_one(user.storage_dict())

                finally:
                    if inserted_result.acknowledged:
                        print("Upserted: %s\t%s\t%s" % (user.full_name, user.username, 
                                                        inserted_result.inserted_id))
                    else:
                        print("ERROR UPSERTING: %s", user_info)


            #Sleep for a bit before getting the next user
            sleep_delay = random.randint(0, 10) # 180))
            time.sleep(sleep_delay)


    @staticmethod
    def default_mongodb(credential_manager=CredentialManager()):
        """Convenience method to return the MongoDB URL (ip, port, username, password)

        Args:
            credential_manager (CredentialManager): CredentialManager object; used for default info

        Returns:
            (str): Mongo Client host (mongo_url://username:password:port)
        """

        mongodb_username, mongodb_password = credential_manager.get_account('InstagramMongoDB')
        mongodb_ip_address, mongodb_port = (credential_manager.
                                            get_values('InstagramMongoDBIPAddress', 
                                                        'InstagramMongoDBPort'))


        mongo_client_host = ("mongodb://{username}:{password}@{ip_address}:{port}/"
                                .format(username=mongodb_username, password=mongodb_password,
                                        ip_address=mongodb_ip_address, port=mongodb_port))

        return mongo_client_host


    @staticmethod
    def default_client():
        """Convenience method to return an Instagram object with the default credentials/set-up

        Returns:
            (:obj: `Instagram.Instagram`): Initialized version of our Instagram client
        """

        credential_manager = CredentialManager()

        current_directory = os.path.abspath(inspect.getfile(inspect.currentframe()))
        save_file_path = os.path.dirname(current_directory)

        insta_username, insta_password = credential_manager.get_account('Instagram')
    
        mongo_client_host = InstagramAnalyzer.default_mongodb(credential_manager)


        client = InstagramAnalyzer(insta_username, insta_password,
                                   mongo_client_host, save_file_path)

        return client


if __name__ == "__main__":
    """ Main method - run from here """

    client = InstagramAnalyzer.default_client()

    client.get_messages()
    exit(0)

    # https://github.com/billcccheng/instagram-terminal-news-feed/blob/master/start.py


    all_followers = client.get_followers(from_mongo=False, from_file=True)
    all_following = client.get_following(from_mongo=False, from_file=True)

    for follower_pk in all_followers:
        if follower_pk in all_following:
            all_following[follower_pk]["is_follower"] = True
            all_followers[follower_pk]["am_following"] = True
            print("Following and followed by: " + all_followers[follower_pk].get("username"))

    client.add_users_to_db(all_followers.keys(), skip_saved=True, is_follower=True, am_following=False)

    exit(0)



    raw_media_info = json.loads(open("media_info.json").read())
    raw_media_info = raw_media_info["items"][0]

    raw_tagged_users = raw_media_info["usertags"]
    tagged_users = []
    print(raw_tagged_users)
    for tag_key, users in raw_tagged_users.items():
        for user_dict in users:
            if "user" in user_dict and "username" in user_dict["user"]:
                user = user_dict["user"]
                tagged_user = {
                    "full_name": user["full_name"],
                    "profile_picture_link": user["profile_pic_url"],
                    "pk": user["pk"],
                    "is_private": user["is_private"],
                    "username": user["username"]
                }
                tagged_users.append(tagged_user)






    """

    client.api.timelineFeed()
    timeline_feed = client.api.LastJson

    for mediaItem in timeline_feed["items"]:

        media_id = mediaItem["id"]
        client.api.mediaInfo(media_id)
        print(json.dumps(client.api.LastJson, indent=4))
        break

    """
