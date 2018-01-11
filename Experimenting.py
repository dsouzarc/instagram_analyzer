"""Experimenting.py: Temporary Python file for testing various experiments before being integrated"""

from collections import Counter

import json
import subprocess
import random
import time

from CredentialManager import CredentialManager
from InstagramAPI import InstagramAPI
from Users import InstagramUser

import pymongo
import requests


#Interactive way to unfollow those who don't follow back
def following_follower_diff(instagram_api):
	"""Convenience method for unfollowing people

	Args:
		instagram_api (InstagramAPI.InstagramAPI): instagram api object
	"""

	all_followers = instagram_api.getTotalSelfFollowers()
	all_following = instagram_api.getTotalSelfFollowings()

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
					unfollow_result = instagram_api.unfollow(user_id)
					print(unfollow_result)

			elif command == 'U' or command == 'u':
				unfollow_result = instagram_api.unfollow(user_id)
				print(unfollow_result)


def get_my_post_likers(instagram_api, save_to_file=True, read_from_file):
    """Goes through all my posts, and for reach post, gets the list of likers

    Returns:
        dict(str, list(dict)): Dictionary with Key: post_id. Value list of likers
    """

    save_file_name = 'results_my_post_likes.json'
    results = dict()

    if read_from_file:
        results = json.load(open(save_file_name, 'r'))
        return results


    my_posts = instagram_api.getTotalSelfUserFeed()

    for post in my_posts:

        post_id = post['pk']

        if 'image_versions2' in post:
            candidates = post['image_versions2']['candidates']
            print("Analyzing: %s\n Caption: %s\n" % (candidates[0]['url'], post['caption'].get('text', '')))


        instagram_api.getMediaLikers(post_id)
        post_likers_info = instagram_api.LastJson
        post_likers = post_likers_info['users']

        results[str(post_id)] = list()

        for post_liker in post_likers:
            liker_pk = str(post_liker['pk'])

            results[str(post_id)].append(post_liker)

        post_url = 'https://www.instagram.com/p/{code}'.format(code=post.get('code'))
        print("Caption: %s\t# of likes: %s\tLink: %s" % (len(post_likers), 
                                                            post['caption'].get('text'), post_url))

        time.sleep(random.randint(2, 10))


    if save_to_file:
        with open(save_file_name, 'w') as save_file:
            json.dump(results, save_file, indent=4)


    return results



#TODO
#liker_counter.update({liker_pk: 1})
#all_likers_map[liker_pk] = post_liker



if __name__ == "__main__":
    """Main method - run from here"""

    credential_manager = CredentialManager()
    insta_username, insta_password = credential_manager.get_account('Instagram')

    instagram_api = InstagramAPI(insta_username, insta_password)

    #following_follower_diff(instagram_api)
    #exit(0)

    #user_info = instagram_api.getUsernameInfo(1458052235)
    #user_info = instagram_api.getUserTags(1458052235)
    #user_info = instagram_api.getGeoMedia(1458052235) #None
    #user_info = instagram_api.getUserFeed(1458052235) #GOOD
    #geo_info = instagram_api.getLikedMedia() #Just things that I've liked


    #instagram_api.mediaInfo('1674292635785098154_1458052235')
    #instagram_api.getMediaLikers('1674292635785098154_1458052235')


    all_followers_map = dict()
    all_likers_map = dict()
    liker_counter = Counter()

    all_followers_raw = instagram_api.getTotalSelfFollowers()
    for raw_follower in all_followers_raw:
        all_followers_map[str(raw_follower['pk'])] = raw_follower

    """
    posts = instagram_api.getTotalSelfUserFeed()

    """

    my_post_likers = get_my_post_likers(instagram_api, save_to_file=True, read_from_file=False)

    all_posts = json.load(open('results_my_likes.json', 'r'))

    for post_id, post_likers in all_posts.items():
        for post_liker in post_likers:
            liker_pk = str(post_liker['pk'])
            liker_counter.update({liker_pk: 1})
            all_likers_map[liker_pk] = post_liker

    for liker_pk, count in liker_counter.most_common():

        user = all_likers_map[liker_pk]
        #print('%s \t\t %s \t\t %s' % (user['username'], user.get('full_name', ''), count)).expandtabs(20)


    for user_pk, user in all_followers_map.items():

        if user_pk not in liker_counter:

            print('%s \t\t %s' % (user['username'], user.get('full_name', ''))).expandtabs(20)
            command = raw_input("Would you like to unfollow and unlike? Enter 'u': ").lower()

            if command == 'u':
                try:
                    user_posts = instagram_api.getTotalUserFeed(user_pk)
                except KeyError:
                    print('Cannot access posts as account could not be found')
                else:
                    unlike_count = 0

                    for user_post in user_posts:
                        if user_post['has_liked']:
                            media_id = user_post['id']
                            unlike_result = instagram_api.unlike(media_id)
                            time.sleep(random.randint(2, 10))

                            if not unlike_result:
                                print("Error unliking post: %s\t %s" % (unlike_result, 
                                        json.dumps(instagram_api.LastJson, indent=4)))
                            else:
                                unlike_count += 1

                    unfollow_result = instagram_api.unfollow(user_pk)

                    print("Unliked %s\tOut of %s. \tUnfollowed: %s" % (unlike_count, len(user_posts), unfollow_result))


            print("\n")



    exit(0)




    """

        for liker_pk, count in liker_counter.most_common():

            user = all_followers_map.get(liker_pk, all_likers_map.get(liker_pk))
            print('%s \t\t %s \t\t %s' % (user['username'], user.get('full_name', ''), count)).expandtabs(20)

        print("\n\nNON-LIKERS \n\n")

        count = 0

        for user_pk, user in all_followers_map.items():
            count += 1 

            if user_pk not in all_likers_map:
                print('%s \t\t %s' % (user['username'], user.get('full_name', ''))).expandtabs(20)

                command = raw_input("Would you like to unfollow and unlike? Enter 'u': ").lower()
                if command == 'u':
                    results = instagram_api.getTotalUserFeed(user_pk)
                    print("RESULTS: %s\n\n" % (json.dumps(results, indent=4)))
                    user_posts_raw = instagram_api.LastJson
                    print("RAW DATA: %s\n\n" % json.dumps(user_posts_raw, indent=4))
                    user_posts = user_posts_raw.get('items')
                    for user_post in user_posts:

                        print(user_post['image_versions2']['candidates'][0])
                    print("HERE: %s\n" % (len(user_posts)))
            if count > 2:
                exit(0)
        exit(0)
    """




    """
    my_post = my_posts[0]

    print(json.dumps(my_post, indent=4))

    results = instagram_api.getMediaLikers('785079885619196477')
    print("LIKES\n\n")
    print(json.dumps(instagram_api.LastJson, indent=4))
    print(json.dumps(results, indent=4))
    """





