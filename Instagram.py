#!/usr/bin/env python

from bson import json_util
from pymongo import MongoClient
from InstagramAPI import InstagramAPI
from Users import InstagramUser

import pymongo
import CredentialManager
import requests

import json
import random
import subprocess
import time


####################################################################
#                   Written by Ryan D'souza
#       	Main class for analyzing Instagram Data
####################################################################


class Instagram(object):


    ####################################################################
    """         Main class that analyzes Instagram data
                    See bottom for run example                      """
    ####################################################################


    IS_DEVELOPMENT = True

    _api = None
    _database = None
    _users_collection = None


    def __init__(self, instagram_username, instagram_password, mongoclient_host):
        """ Constructor
        
            :param instagram_username: string version of username i.e.: 'dsouzarc'
            :param instagram_password: string version of password
            :param mongoclient_host: string host for MongoDB instance i.e.: "localhost://27017"
            
        """

        self._api = InstagramAPI(instagram_username, instagram_password)

        database_client = MongoClient(mongoclient_host)
        self._database = database_client["Instagram"]
        self._users_collection = self._database["users"]

        self._users_collection.create_index("pk", unique=True)


	#Interactive way to unfollow those who don't follow back
    def following_follower_diff(self):
        """ Convenience method for unfollowing people """

        all_followers = self._api.getTotalSelfFollowers()
        
        all_followers = self._api.getTotalSelfFollowers()
        all_following = self._api.getTotalSelfFollowings()

        all_followers_dict = {}

        for follower in all_followers:
            user_id = follower['pk']
            all_followers_dict[user_id] = follower

        for following in all_following:
            user_id = following['pk']

			#The person does not follow us back
            if user_id not in all_followers_dict:

                full_name = following['full_name'].encode('utf-8')
                user_name = following['username'].encode('utf-8')
                profile_link = "https://instagram.com/" + user_name

				#Prompt for unfollowing/other actions
                print(full_name + " not following you: \t " + profile_link)

                command = raw_input("Type 'O' to open in brower, 'U' to unfollow, "
                                        "or any other key to do nothing: ")

                if command == 'O' or command == 'o':
                    subprocess.Popen(['open', profile_link])

                    second_command = raw_input("\nEnter 'U' to unfollow " + full_name + 
                                                    " or any other key to do nothing: ")

                    if second_command == 'U' or second_command == 'u':
                        unfollow_result = self._api.unfollow(user_id)
                        print(unfollow_result)

                elif command == 'U' or command == 'u':
                    unfollow_result = self._api.unfollow(user_id)
                    print(unfollow_result)


    def get_messages(self):
        """ Prints a list of messages in the inbox """

        request_response = self._api.getv2Inbox()
        actual_responses = self._api.LastJson

        inbox = actual_responses["inbox"]
        threads = inbox["threads"]

        for thread in threads:
            thread_users = thread["users"]
            usernames = list()
            for thread_user in thread_users:
                usernames.append(thread_user["username"])
                usernames.append(thread_user["full_name"])

            print("Group chat with: " + ", ".join(usernames))

            sender = thread["inviter"]
            print("From: " + sender["username"] + " " + sender["full_name"])

            messages = thread["items"]
            for message in messages:
                if "text" in message:
                    print(message["text"])
                elif "reel_share" in message:
                    print(message["reel_share"]["text"])
                else:
                    print("Unable to find: " + json.dumps(thread, indent=4))


    #Convenience method
    def get_following(self, from_mongo=True, from_file=False):
        """Gets a list of all the users we are following on Instagram.

            :param from_mongo: bool for whether we should get saved Mongo data or live data
            :param from_file: bool for whether we should get the data from a saved file

            :return dict(pk, dict): dict of who we are following. key: user PK, value: user
        """

        all_following = dict()
        following = list()

        #Get the data from Mongo
        if from_mongo:
            following = self._users_collection.find({'am_following': True})

        #Get the data from a saved file
        elif not from_mongo and from_file:
            saved_following = json.load(open('all_following.json', 'r'))

        #Get the live data
        else:
            following = self._api.getTotalSelfFollowers()
            json.dump(following, open('all_following.json', 'w'), indent=4)


        for saved_following in following:
            saved_following['am_following'] = True
            all_following[saved_following['pk']] = saved_following

        return all_following


    #Convenience method
    def get_followers(self, from_mongo=True, from_file=False):
        """Gets a list of all the users that follow us on Instagram

            :param from_mongo: bool for whether we should get saved Mongo data or live data
            :param from_file: bool for whether we should get the data from a saved file

            :return dict(pk, dict): dict of who follows us. key: user PK, value: user
        """

        all_followers = dict()
        followers = list()

        #Get the data from Mongo
        if from_mongo:
            followers = self._users_collection.find({'is_follower': True})

        #Get the data from a saved file
        elif not from_mongo and from_file:
            followers = json.load(open('all_followers.json', 'r'))

        #Get the live data
        else:
            followers = self._api.getTotalSelfFollowers()
            json.dump(following, open('all_followers.json', 'w'), indent=4)


        for follower in followers:
            follower['is_follower'] = True
            all_followers[follower['pk']] = follower

        return all_followers


    #For adding user information to Mongo
    def add_users_to_db(self, user_pks, skip_saved=True, is_follower=False, am_following=False):
        """Given a list of users, for each user, gets their information (1 API call)
            and saves it to MongoDB

            :param user_pks: list(int) of users' PKs
            :param skip_saved: bool indicating if we should replace the data if it is in Mongo
            :param is_follower: bool indicating if the user follows us
            :param am_following: bool indicating if we follow the user
        """

        skip_user_pks = set()

        #Add the saved user PKs from MongoDB to the Set
        if skip_saved:
            saved_user_pks = self._users_collection.find({}, {'pk': 1})
            for saved_user_pk in saved_user_pks:
                skip_user_pks.add(saved_user_pk)


        for user_pk in user_pks:
            if user_pk not in skip_user_pks:

                try:
                    raw_user_result = self._api.getUsernameInfo(follower_id)
                    raw_user_info = self._api.LastJson
                    raw_user_info = raw_user_info["user"]

                    user = InstagramUser(raw_user_info, 
                                         is_follower=is_follower, 
                                         am_following=am_following)
                    user.add_update("inserted")

                    try:
                        inserted_result = self._users_collection.insert_one(user.storage_dict())

                        if inserted_result.acknowledged is False:
                            print("ERROR INSERTING: %s", user_info)
                        else:
                            print("Inserted: %s\t%s\t%s" % (user.full_name, user.username, 
                                                            inserted_result.inserted_id))

                    #User already exists in MongoDB - let's replace
                    except pymongo.errors.DuplicateKeyError:
                        self._users_collection.delete_one({"pk": user.pk})
                        inserted_result = self._users_collection.insert_one(user.storage_dict())

                        if inserted_result.acknowledged is False:
                            print("ERROR UPDATING: %s", user)
                        else:
                            print("Updated: %s" % inserted_result.inserted_id)

                #Error getting user from Instagram API - sleep then try again
                except requests.exceptions.RequestException as e:
                    print("Requests exception: %s" % (e))
                    all_followers.append(follower)
                    time.sleep(random.randint(180, 10 * 180))


            sleep_delay = random.randint(0, random.randint(6, 8)) # 180))
            print("Sleeping for: %s" % sleep_delay)
            time.sleep(sleep_delay)




if __name__ == "__main__":
    """ Main method - run from here """

    instagram_username = CredentialManager.get_value("InstagramUsername")
    instagram_password = CredentialManager.get_value("InstagramPassword")

    mongodb_username = CredentialManager.get_value("InstagramMongoDBUsername")
    mongodb_password = CredentialManager.get_value("InstagramMongoDBPassword")
    mongodb_ip_address = CredentialManager.get_value("InstagramMongoDBIPAddress")
    mongodb_port = CredentialManager.get_value("InstagramMongoDBPort")

    mongo_client_host = ("mongodb://{username}:{password}@{ip_address}:{port}/"
                            .format(username=mongodb_username, password=mongodb_password,
                                        ip_address=mongodb_ip_address, port=mongodb_port))

    client = Instagram(instagram_username, instagram_password, mongo_client_host)
    client.add_followers_to_db()

    #client.get_messages()
    #client.following_follower_diff()
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
