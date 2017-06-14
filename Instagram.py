from InstagramAPI import InstagramAPI

import json
import subprocess

import CredentialManager

class Instagram:

    api = None

    def __init__(self, instagramUsername, instagramPassword):

        self.api = InstagramAPI(instagramUsername, instagramPassword)
        self.api.login()


    def followingFollowerDiff(self):

        allFollowers = self.api.getTotalSelfFollowers()
        allFollowing = self.api.getTotalSelfFollowings()

        allFollowersDict = {}

        for follower in allFollowers:
            userID = follower['pk']
            allFollowersDict[userID] = follower

        for following in allFollowing:
            userID = following['pk']

            if userID not in allFollowersDict:

                fullName = following['full_name'].encode('utf-8')
                userName = following['username'].encode('utf-8')
                profileLink = "https://instagram.com/" + userName

                print(fullName + " not following you: \t " + profileLink)
                command = raw_input("Type 'O' to open in brower, 'U' to unfollow,  or any other key to do nothing: ")
                if command == 'O' or command == 'o':
                    subprocess.Popen(['open', profileLink])

                    secondCommand = raw_input("\nEnter 'U' to unfollow " + fullName + " or any other key to do nothing: ")

                    if secondCommand == 'U' or secondCommand == 'u':
                        unfollowResult = self.api.unfollow(userID)
                        print(unfollowResult)

                elif command == 'U' or command == 'u':
                    unfollowResult = self.api.unfollow(userID)
                    print(unfollowResult)






if __name__ == "__main__":

    instagramUsername = CredentialManager.get_value("InstagramUsername")
    instagramPassword = CredentialManager.get_value("InstagramPassword")

    client = Instagram(instagramUsername, instagramPassword)

    client.followingFollowerDiff()
    exit(0);

    client.api.timelineFeed()
    timelineFeed = client.api.LastJson

    for mediaItem in timelineFeed["items"]:

        mediaId = mediaItem["id"]
        client.api.mediaInfo(mediaId)
        print(json.dumps(client.api.LastJson, indent=4))
        break


