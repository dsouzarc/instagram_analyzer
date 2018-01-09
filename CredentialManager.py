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


    directory_path = None
    file_path = None
    credentials = None


    def __init__(self):
        """Constructor that just loads the prior credentials to a JSON object"""

        #Store data in hidden file in hidden folder in home directory
        self.directory_path = str(os.path.expanduser('~')) \
                                + '/.my_credential_manager/'
        self.file_path = self.directory_path + '.credential_files.json'

        #Create path if needed
        if not os.path.exists(self.directory_path):
            print('Initialized credential manager: %s' % self.file_path)
            os.makedirs(self.directory_path)

        #Load data from file
        try:
            with open(self.file_path) as credential_file:
                self.credentials = json.load(credential_file)
        except ValueError:
            print 'Error when loading existing credentials. Building new file'
            self.credentials = dict()

        if self.credentials is None:
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

        return base64.b64decode(encrypted_value)


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

    
    def delete_value(self, key, save_credentials=True):
        """Given the key, removes it from the dictionary and saves the file

        Args:
            key (str): Key to delete
            save_credentials (bool): Whether or not to save the dictionary to file
        """

        encrypted_key = self.encrypt_value(key)

        if encrypted_key in self.credentials:
            del self.credentials[encrypted_key]

            if save_credentials:
                self.save_credentials()


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


    def set_value(self, key, value, save_credentials=True):
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


    def save_account(self, account_name, username, password):
        """Given the account name, username, and password, update the credentials dictionary and file with it
        
        Args:
            account_name (str): Name of the account
            username (str): Raw username to save
            password (str): Raw password to save
        """

        username_key = account_name + "_Username"
        password_key = account_name + "_Password"

        self.set_value(username_key, username, save_credentials=False)
        self.set_value(password_key, password, save_credentials=False)
        self.save_credentials()


    def get_account(self, account_name):
        """Given the account name, return the username and password for the account
        
        Args:
            account_name (str): Name of the account

        Returns:
            (list(str)): Username and password for the account
        """

        username_key = account_name + "_Username"
        password_key = account_name + "_Password"

        return self.get_values(username_key, password_key)

    
    def delete_account(self, account_name):
        """Given the account name, deletes the username and password for the account

        Args:
            account_name (str): Name of the account
        """

        username_key = account_name + "_Username"
        password_key = account_name + "_Password"

        self.delete_value(username_key, save_credentials=False)
        self.delete_value(password_key, save_credentials=False)
        self.save_credentials()


    def save_account_prompt(self):
        """Convenience method to prompt and save credentials for an account"""

        account_name = raw_input("Enter name of account: ")
        username = raw_input("Enter account username: ")
        password = getpass.getpass("Enter account password: ")

        self.save_account(account_name, username, password)

    
    def get_account_prompt(self):
        """Convenience method to return credentials for an account"""

        account_name = raw_input("Enter name of account: ")

        credentials = self.get_account(account_name)
        for credential in credentials:
            print(credential)


    def save_value_prompt(self):
        """Convenience method to prompt to save a key and value"""

        key = raw_input("Enter key: ")
        value = raw_input("Enter value: ")

        self.set_value(key, value)


    def get_value_prompt(self):
        """Convenience method to prompt to get a key and value"""

        key = raw_input("Enter key: ")
        print(self.get_value(key))


    def delete_value_prompt(self):
        """Convenience method to delete a key and value"""

        key = raw_input("enter key to delete: ")
        self.delete_value(key)


    def delete_account_prompt(self):
        """Convenience method to delete credentials for an account"""

        account_name = raw_input("Enter name of account to delete: ")
        self.delete_account(account_name)


if __name__ == "__main__":

    manager = CredentialManager()

    if len(sys.argv) == 1:
        manager.save_account_prompt()

    elif len(sys.argv) == 2:
        if sys.argv[1] == "save_account":
            manager.save_account_prompt()
        elif sys.argv[1] == "get_account":
            manager.get_account_prompt()
        elif sys.argv[1] == "save_value":
            manager.save_value_prompt()
        elif sys.argv[1] == "get_value_prompt":
            manager.get_value_prompt()
        elif sys.argv[1] == "delete_account":
            manager.delete_account_prompt()
        elif sys.argv[1] == "delete_value":
            manager.delete_value_prompt()

