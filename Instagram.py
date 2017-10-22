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


    #Warning: Long process - makes a GET request for every follower
    def add_followers_to_db(self):
        """ Gets a list of all the followers on Instagram and for each follower
                Gets the follower's information (1 API call) and saves it to MongoDB
        """

        skip_users_pk = set()


        if self.IS_DEVELOPMENT:
            all_followers = json.load(open("all_followers.json", "r"))

            saved_users_pk = self._users_collection.find({}, {'pk': 1})
            for saved_user_pk in saved_users_pk:
                skip_users_pk.add(saved_user_pk['pk'])

        else:
            all_followers = self._api.getTotalSelfFollowers()
            json.dump(all_followers, open("all_folllowers.json", "w"), indent=4)


        for follower in all_followers:

            follower_id = follower["pk"]

            #If we're in development and we already stored this user, skip them
            if self.IS_DEVELOPMENT and follower_id in skip_users_pk:
                continue

            try:
                raw_user_result = self._api.getUsernameInfo(follower_id)
                raw_user_info = self._api.LastJson
                raw_user_info = raw_user_info["user"]

                user = InstagramUser(raw_user_info)
                user.add_update("inserted")

                try:
                    inserted_result = self._users_collection.insert_one(user.storage_dict())

                    if inserted_result.acknowledged is False:
                        print("ERROR INSERTING: %s", user_info)
                    else:
                        print("Inserted: %s\t%s\t%s" % (user.full_name, user.username, inserted_result.inserted_id))

                except pymongo.errors.DuplicateKeyError:
                    
                    self._users_collection.delete_one({"pk": user.pk})
                    inserted_result = self._users_collection.insert_one(user.storage_dict())

                    if inserted_result.acknowledged is False:
                        print("ERROR UPDATING: %s", user)
                    else:
                        print("Updated: %s" % inserted_result.inserted_id)


            except requests.exceptions.RequestException as e:
                print("Requests exception: %s" % (e))
                all_followers.append(follower)
                time.sleep(random.randint(180, 10 * 180))


            sleep_delay = random.randint(0, random.randint(6, 180))
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
