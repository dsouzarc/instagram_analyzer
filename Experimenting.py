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


def unfollow_user(instagram_api, user_pk, unlike_posts=True, min_wait=2, max_wait=10):
    """Convenience method for unfollowing someone and unliking posts

    Args:
        instagram_api (InstagramAPI.InstagramAPI): instagram api object
        user_pk (str): the user ID/pk
        unlike_posts (bool): whether to unlike their posts
    """

    if not unlike_posts:
        unfollow_result = instagram_api.unfollow(user_pk)
        print("Unfollowed %s" % unfollow_result)
        return
    
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
                time.sleep(random.randint(min_wait, max_wait))

                if not unlike_result:
                    print("Error unliking post: %s\t %s" % (unlike_result, 
                            json.dumps(instagram_api.LastJson, indent=4)))
                else:
                    unlike_count += 1

        unfollow_result = instagram_api.unfollow(user_pk)
        print("Unliked %s\tOut of %s. \tUnfollowed: %s" % (unlike_count, len(user_posts), unfollow_result))


#Interactive way to unfollow those who don't follow back
def following_follower_diff(instagram_api):
    """Interactive method for unfollowing people

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

            command = raw_input("Type 'O' to open in brower, 'U' to unfollow, " + 
                                "'UL' to unfollow and unlike, " + 
                                "or any other key to do nothing: ").lower()

            if command == 'o':
                subprocess.Popen(['open', profile_link])
                
                command = raw_input("\nEnter 'U' to unfollow " + full_name +
                        " or any other key to do nothing: ").lower()
            
            if command == 'u':
                unfollow_user(instagram_api, user_id, unlike_posts=False)
            
            elif command == 'ul':
                unfollow_user(instagram_api, user_id, unlike_posts=True)
                #TODO: Add some sort of Queue for this


def get_my_post_likers(instagram_api, save_to_file=True, read_from_file=False):
    """Goes through all my posts, and for reach post, gets the list of likers

    Returns:
        dict(str, list(dict)): Dictionary with Key: post_id. Value list of likers
    """

    save_file_name = 'results_my_posts_likes.json'
    results = dict()


    if read_from_file:
        results = json.load(open(save_file_name, 'r'))
        return results


    my_posts = instagram_api.getTotalSelfUserFeed()

    for post_counter, post in enumerate(my_posts):

        post_id = post['pk']

        instagram_api.getMediaLikers(post_id)
        post_likers_info = instagram_api.LastJson
        post_likers = post_likers_info['users']

        results[str(post_id)] = list()

        for post_liker in post_likers:
            liker_pk = str(post_liker['pk'])

            results[str(post_id)].append(post_liker)

        post_url = 'https://www.instagram.com/p/{code}'.format(code=post.get('code'))
        print("Caption: %s\t# of likes: %s\nLink: %s" % (len(post_likers), 
                                                            post['caption'].get('text'), post_url))

        time.sleep(random.randint(3, 15))


    if save_to_file:
        with open(save_file_name, 'w') as save_file:
            json.dump(results, save_file, indent=4)


    return results


def get_unique_likers(posts_likers):
    """Given a dictionary of post_ids and a list of their likers,
        Returns a dictionary with the unique likers

    Args:
        post_likers (dict, list((dict)): Results from get_my_post_likers

    Returns:
        dict(str, dict): Dictionary with key: user_id, value: liker
    """

    results = dict()

    for post_id, post_likers in posts_likers.items():
        for post_liker in post_likers:
            results[str(post_liker['pk'])] = post_liker

    return results


def get_liker_frequencies(posts_likers):
    """Given a dictionary of post_ids and a list of their likers,
        Returns a Counter object with user_id and like frequency

    Args:
        posts_likers (dict, list(dict)): Results from get_my_post_likers

    Returns:
        Counter: python Counter object with user_id: frequency
    """

    liker_counter = Counter()

    for post_id, post_likers in posts_likers.items():
        for post_liker in post_likers:
            liker_pk = str(post_liker['pk'])
            liker_counter.update({liker_pk: 1})


    return liker_counter


def get_all_followers(instagram_api, save_to_file=True, read_from_file=False):
    """Convenience method to return a dict with key: username, value: user object

    Returns:
        dict(str, dict): key: username, value: user object
    """

    save_file_name = 'my_followers.json'

    if save_to_file:
        results = json.load(open(save_file_name, 'r'))
        return results
    

    all_followers_map = dict()

    all_followers_raw = instagram_api.getTotalSelfFollowers()
    for raw_follower in all_followers_raw:
        all_followers_map[str(raw_follower['pk'])] = raw_follower

    if save_to_file:
        with open(save_file_name, 'w') as save_file:
            json.dump(all_followers_map, save_file, indent=4)


    return all_followers_map



if __name__ == "__main__":
    """Main method - run from here"""

#TODO: Use .map instead of for for

    credential_manager = CredentialManager()
    insta_username, insta_password = credential_manager.get_account('Instagram')

    instagram_api = InstagramAPI(insta_username, insta_password)

    following_follower_diff(instagram_api)
    exit(0)

    #user_info = instagram_api.getUsernameInfo(1458052235)
    #user_info = instagram_api.getUserTags(1458052235)
    #user_info = instagram_api.getUserFeed(1458052235) #GOOD
    #geo_info = instagram_api.getLikedMedia() #Just things that I've liked



    all_followers_map = get_all_followers(instagram_api, save_to_file=True, read_from_file=True)

    my_posts_likers = get_my_post_likers(instagram_api, save_to_file=True, read_from_file=True)
    unique_likers = get_unique_likers(my_posts_likers)
    liker_frequency = get_liker_frequencies(my_posts_likers)


    for liker_pk, count in liker_frequency.most_common():
        user = unique_likers[str(liker_pk)]
        print('%s \t\t %s \t\t %s' % (user['username'], user.get('full_name', ''), count)).expandtabs(20)


    for user_pk, user in all_followers_map.items():

        if user_pk not in liker_counter:

            print('%s \t\t %s' % (user['username'], user.get('full_name', ''))).expandtabs(20)
            command = raw_input("Would you like to unfollow and unlike? Enter 'u': ").lower()
            if command == 'u':
                unfollow_user(instagram_api, user_pk, unlike_posts=True)



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






