#!/usr/bin/env python

import datetime
import requests
import random
import json
import hashlib
import hmac
import urllib
import uuid
import time
import copy
import pickle
import math
import sys

#Urllib split from Python 2 to Python 3
if sys.version_info.major == 3:
    import urllib.parse

from requests_toolbelt import MultipartEncoder


####################################################################
#                   Modified by Ryan D'souza
#       	Handles interactions with Instagram's API
#			https://github.com/LevPasha/Instagram-API-python
####################################################################


class InstagramAPI(object):


    ####################################################################
    """         Class that acts as an Instagram API Client
                    See Instagram.py for running example			 """
    ####################################################################
    

	#Preferences file
    CONSTANTS_FILE_NAME = "Constants.json"
    REQUESTS_FILE_NAME = "Requests.pkl"
    
	#Other constants
    API_URL = 'https://i.instagram.com/api/v1/'
    USER_AGENT = None
    IG_SIG_KEY = None
    EXPERIMENTS = None
    SIG_KEY_VERSION = None

    username = None
    password = None
    username_id = None
    device_id = None
    uuid = None
    is_logged_in = False
    last_response = None
    session = None
    rank_token = None
    token = None

    last_login_datetime = None

    LastJson = None


    def __init__(self, username, password, debug = False):
        """ Constructor """

        constants_file = open(self.CONSTANTS_FILE_NAME)
        constants = json.load(constants_file)
        constants_file.close()

        self.DEVICE_SETTINGS = constants["DEVICE_SETTINGS"]
        self.USER_AGENT = str(constants["USER_AGENT"]).format(**self.DEVICE_SETTINGS)
        self.IG_SIG_KEY = constants["IG_SIG_KEY"]
        self.EXPERIMENTS = constants["EXPERIMENTS"]
        self.SIG_KEY_VERSION = constants["SIG_KEY_VERSION"]

        self.username = username
        self.password = password
        self.is_logged_in = False
        self.last_response = None

        self.session = requests.session()

        #Get the last time we logged in 
        try:
            datetime_string = constants["last_login_time"]
            self.last_login_datetime = datetime.datetime.strptime(datetime_string, "%Y-%m-%d %H:%M:%S")
            print("FOUND OLD DATE")
        except Exception as date_cast_exception:
            print("EXCEPTION OR NO OLD: %s" % date_cast_exception)
            self.last_login_datetime = None

        #If we logged in under a week ago
        if self.last_login_datetime and (datetime.datetime.now() - self.last_login_datetime).days < 7:
            print("NO LOGIN NEEDED")
            self.is_logged_in = True
            self.username_id = constants["username_id"]
            self.uuid = constants["uuid"]
            self.device_id = constants["device_id"]
            self.rank_token = constants["rank_token"]
            self.token = constants["csrftoken"]

            with open(self.REQUESTS_FILE_NAME, "r") as requests_file:
                self.session = pickle.load(requests_file)


        #If we never logged in or logged in over a week ago
        else:
            print("LOGIN NEEDED")
            m = hashlib.md5()
            m.update(username.encode('utf-8') + password.encode('utf-8'))
            self.device_id = self.generateDeviceId(m.hexdigest())
            self.uuid = self.generateUUID(False)
            #self.uuid = self.generateUUID(True)
            #self.phone_id = self.generateUUID(True)

            if (self.SendRequest('si/fetch_headers/?challenge_type=signup&guid=' + self.uuid, None, True)):

                self.token = self.last_response.cookies['csrftoken']

                print("HERE: %s " % self.last_response)

                data = {
                        'phone_id'   : self.device_id,
                        '_csrftoken' : self.token,
                        'username'   : self.username,
                        'guid'       : self.uuid,
                        'device_id'  : self.device_id,
                        'password'   : self.password,
                        'login_attempt_count' : '0'
                }

                if (self.SendRequest('accounts/login/', self.generateSignature(json.dumps(data)), True)):
                    self.is_logged_in = True
                    self.username_id = self.LastJson["logged_in_user"]["pk"]
                    self.rank_token = "%s_%s" % (self.username_id, self.uuid)
                    self.token = self.last_response.cookies["csrftoken"]
                    self.last_login_datetime = datetime.datetime.now()
                    
                    constants["username_id"] = self.username_id 
                    constants["uuid"] = self.uuid
                    constants["device_id"] = self.device_id
                    constants["rank_token"] = self.rank_token
                    constants["csrftoken"] = self.token
                    constants["last_login_time"] = self.last_login_datetime.strftime("%Y-%m-%d %H:%M:%S")

                    print("DOWN: %s " % self.LastJson)
                    from pprint import pprint
                    pprint(vars(self.session))
                    print("FINISHED")
                    print("Saving : " + json.dumps(constants, indent=4))

                    with open(self.CONSTANTS_FILE_NAME, "w") as constants_file:
                        json.dump(constants, constants_file, ensure_ascii=True, indent=4)

                    with open(self.REQUESTS_FILE_NAME, "wb") as requests_file:
                        pickle.dump(self.session, requests_file, pickle.HIGHEST_PROTOCOL)

                    self.syncFeatures()
                    self.autoCompleteUserList()
                    self.timelineFeed()
                    self.getv2Inbox()
                    self.getRecentActivity()
                    print ("Login success!\n")


    def set_user(self, username, password):
        self.username = username
        self.password = password
        self.uuid = self.generateUUID(True)

    def login(self, force = False):
        if (not self.is_logged_in or force):
            self.session = requests.Session()

            if (self.SendRequest('si/fetch_headers/?challenge_type=signup&guid=' + self.generateUUID(False), None, True)):

                data = {
                        'phone_id'   : self.device_id,
                        '_csrftoken' : self.last_response.cookies['csrftoken'],
                        'username'   : self.username,
                        'guid'       : self.uuid,
                        'device_id'  : self.device_id,
                        'password'   : self.password,
                        'login_attempt_count' : '0'
                }

                if (self.SendRequest('accounts/login/', self.generateSignature(json.dumps(data)), True)):
                    self.is_logged_in = True
                    self.username_id = self.LastJson["logged_in_user"]["pk"]
                    self.rank_token = "%s_%s" % (self.username_id, self.uuid)
                    self.token = self.last_response.cookies["csrftoken"]

                    self.syncFeatures()
                    self.autoCompleteUserList()
                    self.timelineFeed()
                    self.getv2Inbox()
                    self.getRecentActivity()
                    print ("Login success!\n")
                    return True;

    def syncFeatures(self):
        data = json.dumps({
        '_uuid'         : self.uuid,
        '_uid'          : self.username_id,
        'id'            : self.username_id,
        '_csrftoken'    : self.token,
        'experiments'   : self.EXPERIMENTS
        })
        return self.SendRequest('qe/sync/', self.generateSignature(data))

    def autoCompleteUserList(self):
        return self.SendRequest('friendships/autocomplete_user_list/')

    def timelineFeed(self):
        return self.SendRequest('feed/timeline/')

    def megaphoneLog(self):
        return self.SendRequest('megaphone/log/')

    def expose(self):
        data = json.dumps({
        '_uuid'        : self.uuid,
        '_uid'         : self.username_id,
        'id'           : self.username_id,
        '_csrftoken'   : self.token,
        'experiment'   : 'ig_android_profile_contextual_feed'
        })
        return self.SendRequest('qe/expose/', self.generateSignature(data))

    def logout(self):
        logout = self.SendRequest('accounts/logout/')

    def uploadPhoto(self, photo, caption = None, upload_id = None):
        if upload_id is None:
            upload_id = str(int(time.time() * 1000))
        data = {
        'upload_id'         : upload_id,
        '_uuid'             : self.uuid,
        '_csrftoken'        : self.token,
        'image_compression' : '{"lib_name":"jt","lib_version":"1.3.0","quality":"87"}',
        'photo'             : ('pending_media_%s.jpg'%upload_id, open(photo, 'rb'), 'application/octet-stream', {'Content-Transfer-Encoding':'binary'})
        }
        m = MultipartEncoder(data, boundary=self.uuid)
        self.session.headers.update ({'X-IG-Capabilities' : '3Q4=',
                                'X-IG-Connection-Type' : 'WIFI',
                                'Cookie2' : '$Version=1',
                                'Accept-Language' : 'en-US',
                                'Accept-Encoding' : 'gzip, deflate',
                                'Content-type': m.content_type,
                                'Connection' : 'close',
                                'User-Agent' : self.USER_AGENT})
        response = self.session.post(self.API_URL + "upload/photo/", data=m.to_string())
        if response.status_code == 200:
            if self.configure(upload_id, photo, caption):
                self.expose()
        return False

    def uploadVideo(self, video, thumbnail, caption = None, upload_id = None):
        if upload_id is None:
            upload_id = str(int(time.time() * 1000))
        data = {
            'upload_id': upload_id,
            '_csrftoken': self.token,
            'media_type': '2',
            '_uuid': self.uuid,
        }
        m = MultipartEncoder(data, boundary=self.uuid)
        self.session.headers.update({'X-IG-Capabilities': '3Q4=',
                               'X-IG-Connection-Type': 'WIFI',
                               'Host': 'i.instagram.com',
                               'Cookie2': '$Version=1',
                               'Accept-Language': 'en-US',
                               'Accept-Encoding': 'gzip, deflate',
                               'Content-type': m.content_type,
                               'Connection': 'keep-alive',
                               'User-Agent': self.USER_AGENT})
        response = self.session.post(self.API_URL + "upload/video/", data=m.to_string())
        if response.status_code == 200:
            body = json.loads(response.text)
            upload_url = body['video_upload_urls'][3]['url']
            upload_job = body['video_upload_urls'][3]['job']

            videoData = open(video, 'rb').read()
            #solve issue #85 TypeError: slice indices must be integers or None or have an __index__ method
            request_size = int(math.floor(len(videoData) / 4))
            lastRequestExtra = (len(videoData) - (request_size * 3))

            headers = copy.deepcopy(self.session.headers)
            self.session.headers.update({'X-IG-Capabilities': '3Q4=',
                                   'X-IG-Connection-Type': 'WIFI',
                                   'Cookie2': '$Version=1',
                                   'Accept-Language': 'en-US',
                                   'Accept-Encoding': 'gzip, deflate',
                                   'Content-type': 'application/octet-stream',
                                   'Session-ID': upload_id,
                                   'Connection': 'keep-alive',
                                   'Content-Disposition': 'attachment; filename="video.mov"',
                                   'job': upload_job,
                                   'Host': 'upload.instagram.com',
                                   'User-Agent': self.USER_AGENT})
            for i in range(0, 4):
                start = i * request_size
                if i == 3:
                    end = i * request_size + lastRequestExtra
                else:
                    end = (i + 1) * request_size
                length = lastRequestExtra if i == 3 else request_size
                content_range = "bytes {start}-{end}/{lenVideo}".format(start=start, end=(end - 1),
                                                                        lenVideo=len(videoData)).encode('utf-8')

                self.session.headers.update({'Content-Length': str(end - start), 'Content-Range': content_range, })
                response = self.session.post(upload_url, data=videoData[start:start + length])
            self.session.headers = headers

            if response.status_code == 200:
                if self.configureVideo(upload_id, video, thumbnail, caption):
                    self.expose()
        return False

    def direct_share(self, media_id, recipients, text = None):
        # TODO Instagram.php 420-490
        return False

    def configureVideo(self, upload_id, video, thumbnail, caption = ''):
        clip = VideoFileClip(video)
        self.uploadPhoto(photo=thumbnail, caption=caption, upload_id=upload_id)
        data = json.dumps({
            'upload_id': upload_id,
            'source_type': 3,
            'poster_frame_index': 0,
            'length': 0.00,
            'audio_muted': False,
            'filter_type': 0,
            'video_result': 'deprecated',
            'clips': {
                'length': clip.duration,
                'source_type': '3',
                'camera_position': 'back',
            },
            'extra': {
                'source_width': clip.size[0],
                'source_height': clip.size[1],
            },
            'device': self.DEVICE_SETTINGS,
            '_csrftoken': self.token,
            '_uuid': self.uuid,
            '_uid': self.username_id,
            'caption': caption,
        })
        return self.SendRequest('media/configure/?video=1', self.generateSignature(data))

    def configure(self, upload_id, photo, caption = ''):
        #(w,h) = getImageSize(photo)
        (w, h) = (500, 500)
        data = json.dumps({
        '_csrftoken'    : self.token,
        'media_folder'  : 'Instagram',
        'source_type'   : 4,
        '_uid'          : self.username_id,
        '_uuid'         : self.uuid,
        'caption'       : caption,
        'upload_id'     : upload_id,
        'device'        : self.DEVICE_SETTINGS,
        'edits'         : {
            'crop_original_size': [w * 1.0, h * 1.0],
            'crop_center'       : [0.0, 0.0],
            'crop_zoom'         : 1.0
        },
        'extra'         : {
            'source_width'  : w,
            'source_height' : h,
        }})
        return self.SendRequest('media/configure/?', self.generateSignature(data))

    def editMedia(self, mediaId, captionText = ''):
        data = json.dumps({
        '_uuid'        : self.uuid,
        '_uid'         : self.username_id,
        '_csrftoken'   : self.token,
        'caption_text' : captionText
        })
        return self.SendRequest('media/'+ str(mediaId) +'/edit_media/', self.generateSignature(data))

    def removeSelftag(self, mediaId):
        data = json.dumps({
        '_uuid'        : self.uuid,
        '_uid'         : self.username_id,
        '_csrftoken'   : self.token
        })
        return self.SendRequest('media/'+ str(mediaId) +'/remove/', self.generateSignature(data))

    def mediaInfo(self, mediaId):
        data = json.dumps({
        '_uuid'        : self.uuid,
        '_uid'         : self.username_id,
        '_csrftoken'   : self.token,
        'media_id'     : mediaId
        })
        return self.SendRequest('media/'+ str(mediaId) +'/info/', self.generateSignature(data))

    def deleteMedia(self, mediaId):
        data = json.dumps({
        '_uuid'        : self.uuid,
        '_uid'         : self.username_id,
        '_csrftoken'   : self.token,
        'media_id'     : mediaId
        })
        return self.SendRequest('media/'+ str(mediaId) +'/delete/', self.generateSignature(data))
   
    def changePassword(self, newPassword):
        data = json.dumps({
        '_uuid'        : self.uuid,
        '_uid'         : self.username_id,
        '_csrftoken'   : self.token,
        'old_password'  : self.password,
        'new_password1' : newPassword,
        'new_password2' : newPassword
        })
        return self.SendRequest('accounts/change_password/', self.generateSignature(data))
    
    def explore(self):
        return self.SendRequest('discover/explore/')

    def comment(self, mediaId, commentText):
        data = json.dumps({
        '_uuid'        : self.uuid,
        '_uid'         : self.username_id,
        '_csrftoken'   : self.token,
        'comment_text' : commentText
        })
        return self.SendRequest('media/'+ str(mediaId) +'/comment/', self.generateSignature(data))

    def deleteComment(self, mediaId, commentId):
        data = json.dumps({
        '_uuid'        : self.uuid,
        '_uid'         : self.username_id,
        '_csrftoken'   : self.token
        })
        return self.SendRequest('media/'+ str(mediaId) +'/comment/'+ str(commentId) +'/delete/', self.generateSignature(data))

    def changeProfilePicture(self, photo):
        # TODO Instagram.php 705-775
        return False

    def removeProfilePicture(self):
        data = json.dumps({
        '_uuid'        : self.uuid,
        '_uid'         : self.username_id,
        '_csrftoken'   : self.token
        })
        return self.SendRequest('accounts/remove_profile_picture/', self.generateSignature(data))

    def setPrivateAccount(self):
        data = json.dumps({
        '_uuid'        : self.uuid,
        '_uid'         : self.username_id,
        '_csrftoken'   : self.token
        })
        return self.SendRequest('accounts/set_private/', self.generateSignature(data))

    def setPublicAccount(self):
        data = json.dumps({
        '_uuid'        : self.uuid,
        '_uid'         : self.username_id,
        '_csrftoken'   : self.token
        })
        return self.SendRequest('accounts/set_public/', self.generateSignature(data))

    def getProfileData(self):
        data = json.dumps({
        '_uuid'        : self.uuid,
        '_uid'         : self.username_id,
        '_csrftoken'   : self.token
        })
        return self.SendRequest('accounts/current_user/?edit=true', self.generateSignature(data))

    def editProfile(self, url, phone, first_name, biography, email, gender):
        data = json.dumps({
        '_uuid'        : self.uuid,
        '_uid'         : self.username_id,
        '_csrftoken'   : self.token,
        'external_url' : url,
        'phone_number' : phone,
        'username'     : self.username,
        'full_name'    : first_name,
        'biography'    : biography,
        'email'        : email,
        'gender'       : gender,
        })
        return self.SendRequest('accounts/edit_profile/', self.generateSignature(data))

    def getUsernameInfo(self, usernameId):
        return self.SendRequest('users/'+ str(usernameId) +'/info/')

    def getSelfUsernameInfo(self):
        return self.getUsernameInfo(self.username_id)

    def getRecentActivity(self):
        activity = self.SendRequest('news/inbox/?')
        return activity

    def getFollowingRecentActivity(self):
        activity = self.SendRequest('news/?')
        return activity

    def getv2Inbox(self):
        inbox = self.SendRequest('direct_v2/inbox/?')
        return inbox

    def getUserTags(self, usernameId):
        tags = self.SendRequest('usertags/'+ str(usernameId) +'/feed/?rank_token='+ str(self.rank_token) +'&ranked_content=true&')
        return tags

    def getSelfUserTags(self):
        return self.getUserTags(self.username_id)

    def tagFeed(self, tag):
        userFeed = self.SendRequest('feed/tag/'+ str(tag) +'/?rank_token=' + str(self.rank_token) + '&ranked_content=true&')
        return userFeed

    def getMediaLikers(self, mediaId):
        likers = self.SendRequest('media/'+ str(mediaId) +'/likers/?')
        return likers

    def getGeoMedia(self, usernameId):
        locations = self.SendRequest('maps/user/'+ str(usernameId) +'/')
        return locations

    def getSelfGeoMedia(self):
        return self.getGeoMedia(self.username_id)

    def fbUserSearch(self, query):
        query = self.SendRequest('fbsearch/topsearch/?context=blended&query='+ str(query) +'&rank_token='+ str(self.rank_token))
        return query

    def searchUsers(self, query):
        query = self.SendRequest('users/search/?ig_sig_key_version='+ str(self.SIG_KEY_VERSION)
                +'&is_typeahead=true&query='+ str(query) +'&rank_token='+ str(self.rank_token))
        return query

    def searchUsername(self, usernameName):
        query = self.SendRequest('users/'+ str(usernameName) +'/usernameinfo/')
        return query

    def syncFromAdressBook(self, contacts):
        return self.SendRequest('address_book/link/?include=extra_display_name,thumbnails', "contacts=" + json.dumps(contacts))

    def searchTags(self, query):
        query = self.SendRequest('tags/search/?is_typeahead=true&q='+ str(query) +'&rank_token='+ str(self.rank_token))
        return query

    def getTimeline(self):
        query = self.SendRequest('feed/timeline/?rank_token='+ str(self.rank_token) +'&ranked_content=true&')
        return query

    def getUserFeed(self, usernameId, maxid = '', minTimestamp = None):
        query = self.SendRequest('feed/user/' + str(usernameId) + '/?max_id=' + str(maxid) + '&min_timestamp=' + str(minTimestamp)
            + '&rank_token='+ str(self.rank_token) +'&ranked_content=true')
        return query

    def getSelfUserFeed(self, maxid = '', minTimestamp = None):
        return self.getUserFeed(self.username_id, maxid, minTimestamp)

    def getHashtagFeed(self, hashtagString, maxid = ''):
        return self.SendRequest('feed/tag/'+hashtagString+'/?max_id='+str(maxid)+'&rank_token='+self.rank_token+'&ranked_content=true&')

    def searchLocation(self, query):
        locationFeed = self.SendRequest('fbsearch/places/?rank_token='+ str(self.rank_token) +'&query=' + str(query))
        return locationFeed

    def getLocationFeed(self, locationId, maxid = ''):
        return self.SendRequest('feed/location/'+str(locationId)+'/?max_id='+maxid+'&rank_token='+self.rank_token+'&ranked_content=true&')

    def getPopularFeed(self):
        popularFeed = self.SendRequest('feed/popular/?people_teaser_supported=1&rank_token='+ str(self.rank_token) +'&ranked_content=true&')
        return popularFeed

    def getUserFollowings(self, usernameId, maxid = ''):
        return self.SendRequest('friendships/'+ str(usernameId) +'/following/?max_id='+ str(maxid)
            +'&ig_sig_key_version='+ self.SIG_KEY_VERSION +'&rank_token='+ self.rank_token)

    def getSelfUsersFollowing(self):
        return self.getUserFollowings(self.username_id)

    def getUserFollowers(self, usernameId, maxid = ''):
        if maxid == '':
            return self.SendRequest('friendships/'+ str(usernameId) +'/followers/?rank_token='+ self.rank_token)
        else:
            return self.SendRequest('friendships/'+ str(usernameId) +'/followers/?rank_token='+ self.rank_token + '&max_id='+ str(maxid))

    def getSelfUserFollowers(self):
        return self.getUserFollowers(self.username_id)

    def like(self, mediaId):
        data = json.dumps({
        '_uuid'         : self.uuid,
        '_uid'          : self.username_id,
        '_csrftoken'    : self.token,
        'media_id'      : mediaId
        })
        return self.SendRequest('media/'+ str(mediaId) +'/like/', self.generateSignature(data))

    def unlike(self, mediaId):
        data = json.dumps({
        '_uuid'         : self.uuid,
        '_uid'          : self.username_id,
        '_csrftoken'    : self.token,
        'media_id'      : mediaId
        })
        return self.SendRequest('media/'+ str(mediaId) +'/unlike/', self.generateSignature(data))

    def getMediaComments(self, mediaId):
        return self.SendRequest('media/'+ mediaId +'/comments/?')

    def setNameAndPhone(self, name = '', phone = ''):
        data = json.dumps({
        '_uuid'         : self.uuid,
        '_uid'          : self.username_id,
        'first_name'    : name,
        'phone_number'  : phone,
        '_csrftoken'    : self.token
        })
        return self.SendRequest('accounts/set_phone_and_name/', self.generateSignature(data))

    def getDirectShare(self):
        return self.SendRequest('direct_share/inbox/?')

    def backup(self):
        # TODO Instagram.php 1470-1485
        return False

    def follow(self, userId):
        data = json.dumps({
        '_uuid'         : self.uuid,
        '_uid'          : self.username_id,
        'user_id'       : userId,
        '_csrftoken'    : self.token
        })
        return self.SendRequest('friendships/create/'+ str(userId) +'/', self.generateSignature(data))

    def unfollow(self, userId):
        data = json.dumps({
        '_uuid'         : self.uuid,
        '_uid'          : self.username_id,
        'user_id'       : userId,
        '_csrftoken'    : self.token
        })
        return self.SendRequest('friendships/destroy/'+ str(userId) +'/', self.generateSignature(data))

    def block(self, userId):
        data = json.dumps({
        '_uuid'         : self.uuid,
        '_uid'          : self.username_id,
        'user_id'       : userId,
        '_csrftoken'    : self.token
        })
        return self.SendRequest('friendships/block/'+ str(userId) +'/', self.generateSignature(data))

    def unblock(self, userId):
        data = json.dumps({
        '_uuid'         : self.uuid,
        '_uid'          : self.username_id,
        'user_id'       : userId,
        '_csrftoken'    : self.token
        })
        return self.SendRequest('friendships/unblock/'+ str(userId) +'/', self.generateSignature(data))

    def userFriendship(self, userId):
        data = json.dumps({
        '_uuid'         : self.uuid,
        '_uid'          : self.username_id,
        'user_id'       : userId,
        '_csrftoken'    : self.token
        })
        return self.SendRequest('friendships/show/'+ str(userId) +'/', self.generateSignature(data))

    def getLikedMedia(self,maxid=''):
        return self.SendRequest('feed/liked/?max_id='+str(maxid))

    def generateSignature(self, data):
        try:
            parsedData = urllib.parse.quote(data)
        except AttributeError:
            parsedData = urllib.quote(data)

        return 'ig_sig_key_version=' + self.SIG_KEY_VERSION + '&signed_body=' + hmac.new(self.IG_SIG_KEY.encode('utf-8'), data.encode('utf-8'), hashlib.sha256).hexdigest() + '.' + parsedData

    def generateDeviceId(self, seed):
        volatile_seed = "12345"
        m = hashlib.md5()
        m.update(seed.encode('utf-8') + volatile_seed.encode('utf-8'))
        return 'android-' + m.hexdigest()[:16]

    def generateUUID(self, type):
        #according to https://github.com/LevPasha/Instagram-API-python/pull/16/files#r77118894
        #uuid = '%04x%04x-%04x-%04x-%04x-%04x%04x%04x' % (random.randint(0, 0xffff),
        #    random.randint(0, 0xffff), random.randint(0, 0xffff),
        #    random.randint(0, 0x0fff) | 0x4000,
        #    random.randint(0, 0x3fff) | 0x8000,
        #    random.randint(0, 0xffff), random.randint(0, 0xffff),
        #    random.randint(0, 0xffff))
        generated_uuid = str(uuid.uuid4())
        if (type):
            return generated_uuid
        else:
            return generated_uuid.replace('-', '')

    def buildBody(bodies, boundary):
        # TODO Instagram.php 1620-1645
        return False

    def SendRequest(self, endpoint, post = None, login = False):
        if (not self.is_logged_in and not login):
            raise Exception("Not logged in!\n")
            return;

        self.session.headers.update ({'Connection' : 'close',
                                'Accept' : '*/*',
                                'Content-type' : 'application/x-www-form-urlencoded; charset=UTF-8',
                                'Cookie2' : '$Version=1',
                                'Accept-Language' : 'en-US',
                                'User-Agent' : self.USER_AGENT})

        print(self.session.headers)

        from pprint import pprint
        pprint(vars(self.session))

        if (post != None): # POST
            response = self.session.post(self.API_URL + endpoint, data=post) # , verify=False
        else: # GET
            response = self.session.get(self.API_URL + endpoint) # , verify=False

        if response.status_code == 200:
            self.last_response = response
            self.LastJson = json.loads(response.text)
            return True
        else:
            print ("Request return " + str(response.status_code) + " error! " + str(response.json()))
            # for debugging
            try:
                self.last_response = response
                self.LastJson = json.loads(response.text)
            except:
                pass
            return False
            
    def getTotalFollowers(self,usernameId):
        followers = []
        next_max_id = ''
        while 1:
            self.getUserFollowers(usernameId,next_max_id)
            temp = self.LastJson

            for item in temp["users"]:
                followers.append(item)

            if temp["big_list"] == False:
                return followers            
            next_max_id = temp["next_max_id"]         

    def getTotalFollowings(self,usernameId):
        followers = []
        next_max_id = ''
        while 1:
            self.getUserFollowings(usernameId,next_max_id)
            temp = self.LastJson

            for item in temp["users"]:
                followers.append(item)

            if temp["big_list"] == False:
                return followers            
            next_max_id = temp["next_max_id"] 

    def getTotalUserFeed(self, usernameId, minTimestamp = None):
        user_feed = []
        next_max_id = ''
        while 1:
            self.getUserFeed(usernameId, next_max_id, minTimestamp)
            temp = self.LastJson
            for item in temp["items"]:
                user_feed.append(item)
            if temp["more_available"] == False:
                return user_feed
            next_max_id = temp["next_max_id"]

    def getTotalSelfUserFeed(self, minTimestamp = None):
        return self.getTotalUserFeed(self.username_id, minTimestamp) 
    
    def getTotalSelfFollowers(self):
        return self.getTotalFollowers(self.username_id)
    
    def getTotalSelfFollowings(self):
        return self.getTotalFollowings(self.username_id)
        
    def getTotalLikedMedia(self,scan_rate = 1):
        next_id = ''
        liked_items = []
        for x in range(0,scan_rate):
            temp = self.getLikedMedia(next_id)
            temp = self.LastJson
            next_id = temp["next_max_id"]
            for item in temp["items"]:
                liked_items.append(item)
        return liked_items
