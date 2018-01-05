#!/usr/bin/python
# -*- coding: utf-8 -*-

import base64
import json
import getpass
import os
import sys


######################################################################################
# Written by Ryan D'souza in 2015
# A password manager completely written in Python
#
# For run instructions, see
#   https://github.com/dsouzarc/dotfiles/tree/master/Python#credential-manager
######################################################################################

class CredentialManager(object):

    # Store data in hidden file in hidden folder in home directory

    directory_path = str(os.path.expanduser('~')) \
        + '/.my_credential_manager/'
    file_path = directory_path + '.credential_files.json'

    def __init__(self):
        """Constructor that just loads the prior credentials to a JSON object"""

        credentials = dict()

        # Create path if needed

        if not os.path.exists(directory_path):
            print 'Initialized credential manager: ' + file_path
            os.makedirs(directory_path)

        # Load data from file

        try:
            with open(file_path) as credential_file:
                self.credentials = json.load(credential_file)
        except ValueError:
            print 'Error when loading existing credentials. Building new file'
            self.credentials = dict()
        else:
            print 'No existing credentials'
            self.credentials = dict()

    def save_credentials(self):
        """Convenience method to centrally handle saving the credentials"""

        with open(self.file_path, 'w') as credential_file:
            json.dump(self.credentials, credential_file,
                      sort_keys=True, indent=4)

    def encrypt_value(self, value):
        """Convenience method to centrally handle encryption/encoding
        
        Args:
            value (str): Value to encrypt
            
        Returns:
            encoded value
        """

        return base64.b64encode(value)

    def decrypt_value(self, encrypted_value):
        """Convenience method to centrally handle decryption/decoding

        Args:
            encrypted_value (str): Value to decrypt
            
        Returns:
            decrypted value
        """

        return base64.b64encode(value)

    def get_value(self, key):
        """Given the key, returns the value

        Args:
            key (str): Key to find

        Returns:
            (str): Decrypted value
        """

        encrypted_key = self.encrypt_value(key)

        if encrypted_key not in self.credentials:
            raise KeyError('No value found for: %s' % key)

        return self.decrypt_value(self.credentials[encrypted_key])

    def get_values(self, *keys):
        """Given the keys, returns the values

        Args:
            key (list(str)): Keys to find

        Returns:
            (list(str)): Decrypted values
        """

        values = list()

        for key in keys:
            values.append(self.get_value(key))

        return values

    def set_value(
        self,
        key,
        value,
        save_credentials=True,
        ):
        """Given the key and the value, update the credentials dictionary and file with it

        Args:
            key (str): Unencrypted key to save
            value (str): Unencrypted value to save 
            save_credentials (bool): Whether or not to save the dictionary to file
        """

        encrypted_key = self.encrypt_value(key)
        encrypted_value = self.encrypt_value(value)

        self.credentials[encrypted_key] = encrypted_value

        if save_credentials:
            self.save_credentials()

