from bson import json_util
from datetime import datetime

import json


####################################################################
#                   Written by Ryan D'souza
#       	Represents an Instagram User stored in MongoDB
####################################################################


def get_datetime():
    """ Convenience method for current date as a string

        :return: string for today in YYYY-MM-dd
    """
    return datetime.now().strftime('%Y-%m-%d')



class InstagramUser(object):
    """
        Represents an InstagramUser stored in MongoDB
        Object-Oriented design for convenience and encapsulation when manipulating
            more complicated data which might be missing
    """

    full_name = None
    profile_picture_link = None
    following_count = None
    follower_count = None
    biography = None
    pk = None
    username = None
    is_private = False
    is_business = False
    is_follower = False
    am_following = False

    last_updated = None
    updates = None
    states = None


    def __init__(self, raw_user_info, last_updated=None, updates=None, 
                    states=None, is_follower=False, am_following=False):
        """
            Constructor
                :param raw_user_info: dict JSON response from Instagram getUsernameInfo API call
                :param last_updated: string YYY-MM-dd for when this user was last updated
                :param updates: dict{string date: list(operation)} for when/what we did
                :param states: dict{string date: json difference} 
                :param is_follower: bool indicating whether or not they follow us
                :param am_following: bool indicating whether or not we follow them
        """

        self.full_name = raw_user_info["full_name"]
        self.profile_picture_link = raw_user_info["hd_profile_pic_url_info"]["url"]
        self.following_count = raw_user_info["following_count"]
        self.follower_count = raw_user_info["follower_count"]
        self.biography = raw_user_info["biography"]
        self.pk = raw_user_info["pk"]
        self.username = raw_user_info["username"]
        self.is_private = raw_user_info["is_private"]
        self.is_business = raw_user_info["is_business"]

        self.is_follower = is_follower
        self.am_following = am_following


        if last_updated is None:
            self.last_updated = raw_user_info.get("last_updated", get_datetime())
        else:
            self.last_updated = get_datetime()

        if updates is None:
            self.updates = raw_user_info.get("updates", dict())
        else:
            self.updates = dict()

        if states is None:
            self.states = raw_user_info.get("states", dict())
        else:
            self.states = dict()


    def add_update(self, update, current_date=get_datetime()):
        """
            Adds an update to this user with the current date as a key

                :param update: string description of the update
        """
        
        if current_date not in self.updates:
            self.updates[current_date] = list()

        self.updates[current_date].append(update)
        self.last_updated = current_date


    def add_state(self, state, current_date=get_datetime()):
        """
            Adds the old state of this user with the current date as a key

                :param state: dict of user
        """

        self.states[current_date] = state
        self.last_updated = current_date


    def storage_dict(self):
        return vars(self)

