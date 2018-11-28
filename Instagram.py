#!/usr/bin/env python
"""Instagram.py: Handles interacting with Instagram API, adds additional functionality"""

import inspect
import json
import os
import random
import subprocess
import sys
import time

from bson import json_util
from CredentialManager import CredentialManager
from InstagramAPI import InstagramAPI
from pymongo import MongoClient
from Users import InstagramUser

import pymongo
import requests


####################################################################
#                   Written by Ryan D'souza
#       	Main class for interacting with Instagram
####################################################################



class Instagram(InstagramAPI):
    """Main class that handles all interactions"""


    def __init__(self, insta_username, insta_password, save_file_path=None):
        """Constructor

        Args:
            insta_username (str): string version of username i.e.: 'dsouzarc'
            insta_password (str): string version of password
            save_file_path (str): string path to where we should save the credentials
        """

        InstagramAPI.__init__(self, username=insta_username, password=insta_password, 
                              save_file_path=save_file_path)


    def get_messages(self):
        """Prints a list of messages in the inbox"""

        request_response = self.getv2Inbox()
        actual_responses = self.LastJson

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

                elif "items" in thread:
                    descriptions = list()
                    for item in thread["items"]:
                        if "action_log" in item:
                            descriptions.append(item["action_log"])
                        elif "media_share" in item:
                            media_url = 'https://instagram.com/p/' + item['media_share']['code']
                            descriptions.append(media_url)

                    print(' \t'.join(str(description) for description in descriptions))

                else:
                    print("Unable to find: " + json.dumps(thread, indent=4))


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
    

        client = Instagram(insta_username, insta_password, save_file_path)

        return client


if __name__ == "__main__":
    """ Main method - run from here """

    client = Instagram.default_client()

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
