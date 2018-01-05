#!/usr/bin/python

import base64
import json
import getpass 
import os
import sys

"""Note: This is not a secure password manager for production purposes.
    It sacrifices security at the expense of convenience and quicker speed.
    I mainly use it as a fast way to access (centralized) credentials for my personal side projects
"""


######################################################################################
# Written by Ryan D'souza in 2015
# A password manager completely written in Python
#
# For run instructions, see
#   https://github.com/dsouzarc/dotfiles/tree/master/Python#credential-manager 
######################################################################################


#Store data in hidden file in hidden folder in home directory
directory_path = str(os.path.expanduser("~")) + "/.my_credential_manager/"
file_path = directory_path + ".credential_files.json"

#Create path if needed
if not os.path.exists(directory_path):
    print("Initialized credential manager: " + file_path)
    os.makedirs(directory_path)

#Load data from file
if os.path.isfile(file_path):
    try:
        with open(file_path) as credential_file:
            credentials = json.load(credential_file)
    except ValueError:
        print("Value error for loading existing credentials from file. Building new file")
        credentials = {}
else:
    print("No existing credentials")
    credentials = {}


#################################
# UTILITY & MANAGERIAL METHODS
#################################


def save_credentials_prompt():
    """Prompts user to enter username and password for an account and then saves it"""
    account_name = raw_input("Enter account name: ")
    username_raw = raw_input("Enter username for account: ")
    password_raw = getpass.getpass("Enter password for account: ")

    username_key = account_name + "_Username"
    password_key = account_name + "_Password"

    save_credentials(username_key, username_raw, password_key)


def get_credentials(account_name):
    """Retrieves the (username, password) as a tuple for the given account name

    Args:
        account_name (str): Name of the service 

    Returns:
        tuple(str, str): Username and password for the service
    """

    username_key = account_name + "_Username"
    password_key = account_name + "_Password"

    username = get_value(username_key)
    password = get_value(password_key)

    return (username, password)

def get_credentials_prompt():
    """Prompts the user to enter an account name. Prints the credentials"""

    account_name = raw_input("Enter account name: ")
    username, password = get_credentials(account_name)

    print(username)
    print(password)


#Save credentials
def save_credentials(usernameKey, username, password, passwordKey):
    
    if usernameKey in credentials:
        print("Username already exists for '" + usernameKey + "'.")
        answer = raw_input("Override? y/n: ")

        if answer == 'y':
            credentials[usernameKey] = base64.b64encode(username)
            credentials[passwordKey] = base64.b64encode(password)

            with open(file_path, 'w') as file:
                json.dump(credentials, file, sort_keys = True, indent = 4, ensure_ascii = False)
                print("Credentials saved")
                return
        else:
            print("Cancelled")
            return
    else:
        credentials[usernameKey] = base64.b64encode(username)
        credentials[passwordKey] = base64.b64encode(password)
        
        with open(file_path, 'w') as file:
            json.dump(credentials, file, sort_keys = True, indent = 4, ensure_ascii = False)
            print("Credentials saved")
            return


#Set key to value
def save_key(key, value):
    credentials[key] = base64.b64encode(value)
    
    with open(file_path, 'w') as file:
        json.dump(credentials, file, sort_keys = True, indent = 4, ensure_ascii = False)
        print("Key and value successfully saved")

#Save key to value (with secure prompt)
def save_key_prompt():
    key = raw_input("Key: ")
    value = raw_input("Value: ")

    save_key(key, value)


#Get value/credential associated with key
def get_value(key):

    if key in credentials:
        return base64.b64decode(credentials[key])
    else:
        raise KeyError("No value found for: " + key)

def get(key):
    return get_value(key)

def get_value_prompt():
    return get_value(raw_input("Enter key: "))

#Check to see if a value/credential exists
def does_key_exist(key):
    return key in credentials

def does_key_exist_prompt():
    return does_key_exist(raw_input("Enter key: "))

#Delete a credential
def delete_key(key):

    if key in credentials:
        del credentials[key]
        
        with open(file_path, 'w') as file:
            json.dump(credentials, file, sort_keys = True, indent = 4, ensure_ascii = False)
            print("Value for '" + key + "' has been deleted. Credentials saved")
            return
        print("Error saving credentials")
    else:
        print("Delete failed '" + key + "' does not exist")

def delete_key_prompt():
    delete_key(raw_input("Enter key to delete: "))

#Prompts for credentials, then saves them
def save_credentials_prompt():
    usernameKey = raw_input("Username key: ")   
    username = raw_input("Username: ")
    passwordKey = raw_input("Password key: ")
    password = getpass.getpass("Password: ")

    save_credentials(usernameKey, username, password, passwordKey)

#Only prompt for credentials and then save them if this file is run from main ( 'python CredentialManager.py' )
if __name__ == "__main__":

    if len(sys.argv) == 1:
        save_credentials_prompt()

    elif len(sys.argv) == 2:

        if sys.argv[1] == "save_credentials":
            save_credentials_prompt()
        elif sys.argv[1] == "save_key":
            save_key_prompt()
        elif sys.argv[1] == "set_value":
            save_key_prompt()

        elif sys.argv[1] == "get_credentials":
            get_credentials_prompt()
        elif sys.argv[1] == "get_value":
            print(get_value_prompt())
        elif sys.argv[1] == "does_key_exist":
            print(does_key_exist_prompt())
        elif sys.argv[1] == "delete_key":
            delete_key_prompt()
