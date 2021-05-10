from os.path import exists
from pathlib import Path
import argparse
import getpass
import json
import sys

import praw

import config

DATA_DIRECTORY_NAME = 'data'
FILE_OVERWRITE_MESSAGE_SUFFIX = ' already exists. Do you want to overwrite it?'
GET_ACCOUNT_CREDENTIALS_MESSAGE_PREFIX = 'Enter account credentials for '
REDDIT_OVERWRITE_MESSAGE = 'Do you want to upload this data to your Reddit account?'
USER_AGENT = 'reddit-account-migration'

multireddits_filename = f'{DATA_DIRECTORY_NAME}/multireddits.json'
subreddits_filename = f'{DATA_DIRECTORY_NAME}/subreddits.json'


def confirm_exists(filename):
    """Print an error message and exit if the filename doesn't exist.
    
    Keyword arguments:
    filename -- the filename
    """
    if not exists(filename):
        exit_script(f"Error: {filename} doesn't exist. Exiting.")


def confirm_overwrite(message):
    """Prompt the user to confirm if the resource should be overwritten and exit if not.
    
    Keyword arguments:
    message -- the message to prompt the user with
    """
    print(message)
    user_input = input('(y/n)\n> ')
    if user_input != 'y':
        exit_script()


def download_multireddits_from_reddit(reddit):
    """Download multireddits from Reddit and return them.
    
    Keyword arguments:
    reddit -- the PRAW Reddit instance
    """
    print('Downloading multireddits from Reddit')
    multireddits = reddit.user.multireddits()
    multireddits_list = []
    for multireddit in multireddits:
        subreddits = []
        [subreddits.append(subreddit.display_name) for subreddit in multireddit.subreddits]        
        multireddits_list.append({
            'displayName': multireddit.display_name,
            'subreddits': subreddits,
            'visibility': multireddit.visibility,
        })
        print('Multireddits downloaded:', len(multireddits_list))
    print('Total multireddits downloaded:', len(multireddits_list))
    return multireddits_list


def download_subreddits_from_reddit(reddit):
    """Download subreddits from Reddit and return them.
    
    Keyword arguments:
    reddit -- the PRAW Reddit instance
    """
    print('Downloading subreddits from Reddit')
    subreddits = reddit.user.subreddits(limit=None)
    subreddits_list = []
    for subreddit in subreddits:
        subreddits_list.append(subreddit.display_name)
        print('Subreddits downloaded:', len(subreddits_list))
    print('Total subreddits downloaded:', len(subreddits_list))
    return subreddits_list


def exit_script(message=None):
    """Print a message and exit.
    
    Keyword arguments:
    message -- the message to print before exiting (default None)
    """
    if message:
        print(message)
    else:
        print('Exiting')
    sys.exit()


def get_account_credentials(message):
    """Prompt the user to enter their Reddit account credentials and return them.
    
    Keyword arguments:
    message -- the message to prompt the user with
    """
    print(message)
    username = input('Username\n> ')
    confirm_password, password = get_password()
    while confirm_password != password:
        print("Passwords don't match. Try again? (y/n)")
        user_input = input('> ')
        if user_input == 'n':
            exit_script()
        confirm_password, password = get_password()
    return (password, username)


def get_multireddits_from_file():
    """Get multireddits from file and return them."""
    confirm_exists(multireddits_filename)
    with open(multireddits_filename) as f:
        dictionary = json.load(f)
        multireddits = dictionary['multireddits']
        return multireddits


def get_password():
    """Prompt the user to enter their Reddit account password and return it."""
    print('Password\n> ', end='')
    password = getpass.getpass(prompt='')
    print('Confirm password\n>', end='')
    confirm_password = getpass.getpass(prompt='')
    return (confirm_password, password)


def get_subreddits_from_file():
    """Get subreddits from file and return them."""
    confirm_exists(subreddits_filename)
    with open(subreddits_filename) as f:
        dictionary = json.load(f)
        subreddits = dictionary['subreddits']
        return subreddits


def upload_multireddits_to_reddit(multireddits, reddit, should_overwrite):
    """Upload multireddits to Reddit, skipping any multireddit that already exists.
    
    Keyword arguments:
    multireddits -- the multireddits to upload to Reddit
    reddit -- the PRAW Reddit instance
    should_overwrite -- whether or not the function should upload the multireddits to Reddit without confirming
    """
    print('Downloading existing multireddits to prevent collisions')
    existing_multireddits = download_multireddits_from_reddit(reddit)
    existing_multireddits = [existing_multireddit['displayName'] for existing_multireddit in existing_multireddits]
    print('Uploading multireddits to Reddit')
    if not should_overwrite:
        confirm_overwrite(REDDIT_OVERWRITE_MESSAGE)
    multireddits_uploaded_count = 0
    for multireddit in multireddits:
        if multireddit['displayName'] in existing_multireddits:
            print(f'Multireddit {multireddit["displayName"]} already exists, skipping')
            continue
        reddit.multireddit.create(multireddit['displayName'], multireddit['subreddits'], visibility=multireddit['visibility'])
        multireddits_uploaded_count += 1
        print('Multireddits uploaded:', multireddits_uploaded_count)
    print('Total multireddits uploaded:', multireddits_uploaded_count)


def upload_subreddits_to_reddit(reddit, should_overwrite, subreddits):
    """Upload subreddits to Reddit.
    
    Keyword arguments:
    reddit -- the PRAW Reddit instance
    should_overwrite -- whether or not the function should upload the subreddits to Reddit without confirming
    subreddits -- the subreddits to upload to Reddit
    """
    print('Uploading subreddits to Reddit')
    if not should_overwrite:
        confirm_overwrite(REDDIT_OVERWRITE_MESSAGE)
    subreddit_model_list = [reddit.subreddit(subreddit) for subreddit in subreddits[1:]]
    reddit.subreddit(subreddits[0]).subscribe(other_subreddits=subreddit_model_list)
    print('Uploaded all subreddits')


def write_multireddits_to_file(multireddits, should_overwrite):
    """Write multireddits to file.
    
    Keyword arguments:
    multireddits -- the multireddits to save to the file
    should_overwrite -- whether or not the function should write the multireddits to the file without confirming
    """
    dictionary = {
        'multireddits': multireddits
    }
    Path(DATA_DIRECTORY_NAME).mkdir(exist_ok=True, parents=True)
    if not should_overwrite and exists(multireddits_filename):
        confirm_overwrite(f'{multireddits_filename}{FILE_OVERWRITE_MESSAGE_SUFFIX}')
    with open(multireddits_filename, 'w') as f:
        json.dump(dictionary, f)


def write_subreddits_to_file(should_overwrite, subreddits):
    """Write subreddits to file.
    
    Keyword arguments:
    should_overwrite -- whether or not the function should write the subreddits to the file without confirming
    subreddits -- the subreddits to save to the file
    """
    dictionary = {
        'subreddits': subreddits
    }
    Path(DATA_DIRECTORY_NAME).mkdir(exist_ok=True, parents=True)
    if not should_overwrite and exists(subreddits_filename):
        confirm_overwrite(f'{subreddits_filename}{FILE_OVERWRITE_MESSAGE_SUFFIX}')
    with open(subreddits_filename, 'w') as f:
        json.dump(dictionary, f)


parser = argparse.ArgumentParser()
parser.add_argument('-d', '--download', action='store_true', help='Download data')
parser.add_argument('-u', '--upload', action='store_true', help='Upload data')
parser.add_argument('-o', '--overwrite', action='store_true', help='Overwrite data (local data or Reddit data) without confirming')
args = parser.parse_args()

if args.download:
    account_credentials = None
    if hasattr(config, 'DOWNLOAD_PASSWORD') and hasattr(config, 'DOWNLOAD_USERNAME'):
        account_credentials = (config.DOWNLOAD_PASSWORD, config.DOWNLOAD_USERNAME)
    else:
        account_credentials = get_account_credentials(f'{GET_ACCOUNT_CREDENTIALS_MESSAGE_PREFIX}download:')
    reddit = praw.Reddit(
        client_id=config.DOWNLOAD_CLIENT_ID,
        client_secret=config.DOWNLOAD_CLIENT_SECRET,
        password=account_credentials[0],
        user_agent=USER_AGENT,
        username=account_credentials[1],
    )
    multireddits = download_multireddits_from_reddit(reddit)
    write_multireddits_to_file(multireddits, args.overwrite)
    subreddits = download_subreddits_from_reddit(reddit)
    write_subreddits_to_file(args.overwrite, subreddits)

if args.upload:
    account_credentials = None
    if hasattr(config, 'UPLOAD_PASSWORD') and hasattr(config, 'UPLOAD_USERNAME'):
        account_credentials = (config.UPLOAD_PASSWORD, config.UPLOAD_USERNAME)
    else:
        account_credentials = get_account_credentials(f'{GET_ACCOUNT_CREDENTIALS_MESSAGE_PREFIX}upload:')
    reddit = praw.Reddit(
        client_id=config.UPLOAD_CLIENT_ID,
        client_secret=config.UPLOAD_CLIENT_SECRET,
        password=account_credentials[0],
        user_agent=USER_AGENT,
        username=account_credentials[1],
    )
    multireddits = get_multireddits_from_file()
    upload_multireddits_to_reddit(multireddits, reddit, args.overwrite)
    subreddits = get_subreddits_from_file()
    upload_subreddits_to_reddit(reddit, args.overwrite, subreddits)