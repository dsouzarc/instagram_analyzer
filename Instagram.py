#!/usr/bin/env python

import json
import subprocess

import CredentialManager
from InstagramAPI import InstagramAPI


####################################################################
#                   Written by Ryan D'souza
#       	Main class for analyzing Instagram Data
####################################################################


class Instagram(object):


    ####################################################################
    """         Main class that analyzes Instagram data
                    See bottom for run example                      """
    ####################################################################


    _api = None


    def __init__(self, instagram_username, instagram_password):
        """ Constructor """

        self._api = InstagramAPI(instagram_username, instagram_password)


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
                command = raw_input("Type 'O' to open in brower, 'U' to unfollow,  or any other key to do nothing: ")
                if command == 'O' or command == 'o':
                    subprocess.Popen(['open', profile_link])

                    second_command = raw_input("\nEnter 'U' to unfollow " + full_name + " or any other key to do nothing: ")

                    if second_command == 'U' or second_command == 'u':
                        unfollow_result = self._api.unfollow(user_id)
                        print(unfollow_result)

                elif command == 'U' or command == 'u':
                    unfollow_result = self._api.unfollow(user_id)
                    print(unfollow_result)



if __name__ == "__main__":

    instagram_username = CredentialManager.get_value("InstagramUsername")
    instagram_password = CredentialManager.get_value("InstagramPassword")

    client = Instagram(instagram_username, instagram_password)


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
    raw_user_info = json.loads(open("user_info.json").read())
    raw_user_info = raw_user_info["user"]

    user_info = {}
    user_info["name"] = raw_user_info["full_name"]
    user_info["profile_picture_link"] = raw_user_info["hd_profile_pic_url_info"]["url"]
    user_info["following_count"] = raw_user_info["following_count"]
    user_info["follower_count"] = raw_user_info["follower_count"]
    user_info["biography"] = raw_user_info["biography"]
    user_info["pk"] = raw_user_info["pk"]
    user_info["username"] = raw_user_info["username"]
    user_info["is_private"] = raw_user_info["is_private"]
    user_info["is_business"] = raw_user_info["is_business"]

    print(json.dumps(user_info, indent=4))

    """

    """

    client.api.timelineFeed()
    timeline_feed = client.api.LastJson

    for mediaItem in timeline_feed["items"]:

        media_id = mediaItem["id"]
        client.api.mediaInfo(media_id)
        print(json.dumps(client.api.LastJson, indent=4))
        break

    """
