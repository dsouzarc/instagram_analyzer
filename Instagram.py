from InstagramAPI import InstagramAPI

import json

import CredentialManager

class Instagram:

    api = None

    def __init__(self, instagramUsername, instagramPassword):

        self.api = InstagramAPI(instagramUsername, instagramPassword)
        self.api.login()


    def followingFollowerDiff(self):


        print("GOT MY ID: " + str(self.api.username_id))
        self.api.getUserFollowers(self.api.username_id, 500)

        print(json.dumps(self.api.LastJson, indent=4))





if __name__ == "__main__":

    instagramUsername = CredentialManager.get_value("InstagramUsername")
    instagramPassword = CredentialManager.get_value("InstagramPassword")

    client = Instagram(instagramUsername, instagramPassword)

    client.followingFollowerDiff()


    #api.timelineFeed()

    #print(json.dumps(api.LastJson, indent=4))
