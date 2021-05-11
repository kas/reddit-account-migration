from os.path import exists
from pathlib import Path
import argparse
import getpass
import json
import sys
import time

import praw

import config

# to do handle invalid password
# to do handle invalid username
# to do add blocked users

DATA_DIRECTORY_NAME = 'data'
FILE_OVERWRITE_MESSAGE_SUFFIX = ' already exists. Do you want to overwrite it?'
FOUND_ACCOUNT_CREDENTIALS_MESSAGE = 'Found account credentials from config.py'
GET_ACCOUNT_CREDENTIALS_MESSAGE_PREFIX = '\nEnter account credentials for '
REDDIT_OVERWRITE_MESSAGE = '\nDo you want to upload this data to your Reddit account?'
USER_AGENT = 'reddit-account-migration'

multireddits_filename = f'{DATA_DIRECTORY_NAME}/multireddits.json'
skipped_resources_filename = f'{DATA_DIRECTORY_NAME}/skipped-resources.json'
subreddits_filename = f'{DATA_DIRECTORY_NAME}/subreddits.json'


def confirm_exists(filename):
    """Print an error message and exit if the filename doesn't exist.
    
    Keyword arguments:
    filename -- the filename
    """
    if not exists(filename):
        exit_script(f"Error: {filename} doesn't exist. Exiting.")
 

def download_multireddits_from_reddit(reddit, should_prepend_newline=True):
    """Download multireddits from Reddit and return them.
    
    Keyword arguments:
    reddit -- the PRAW Reddit instance
    should_prepend_newline -- whether or not to prepend the first print statement with a newline (default True)
    """
    print_message_prepend_newline('Downloading multireddits from Reddit', should_prepend_newline)
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
    print('\nDownloading subreddits from Reddit')
    subreddits = reddit.user.subreddits(limit=None)
    subreddits_list = []
    for subreddit in subreddits:
        subreddits_list.append({
            'displayName': subreddit.display_name,
            'isQuarantined': subreddit.quarantine,
            'subredditType': subreddit.subreddit_type,
        })
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
    print('Confirm password\n> ', end='')
    confirm_password = getpass.getpass(prompt='')
    return (confirm_password, password)


def get_subreddits_from_file():
    """Get subreddits from file and return them."""
    confirm_exists(subreddits_filename)
    with open(subreddits_filename) as f:
        dictionary = json.load(f)
        subreddits = dictionary['subreddits']
        return subreddits


def print_message_prepend_newline(message, should_prepend_newline=True):
    """Print a message prepended by a newline.
    
    Keyword arguments:
    message -- the message to print
    should_prepend_newline -- whether or not to prepend the message with a newline (default True)
    """
    message = f'\n{message}' if should_prepend_newline else message
    print(message)


def should_overwrite(message=REDDIT_OVERWRITE_MESSAGE, reddit=None):
    """Return whether or not the resource should be overwritten.
    
    Keyword arguments:
    message -- the message to prompt the user with (default REDDIT_OVERWRITE_MESSAGE)
    reddit -- the PRAW Reddit instance (default None)
    """
    if not args.overwrite:
        print(message)
        if reddit:
            print('Reddit account:', reddit.user.me().name)
        user_input = input('(y/n)\n> ')
        return user_input == 'y'
    return True


def upload_multireddits_to_reddit(multireddits, reddit):
    """Upload multireddits to Reddit, skipping any multireddit that already exists.
    
    Keyword arguments:
    multireddits -- the multireddits to upload to Reddit
    reddit -- the PRAW Reddit instance
    """
    print('\nUploading multireddits to Reddit')
    print('Downloading existing multireddits to prevent collisions')
    existing_multireddits = download_multireddits_from_reddit(reddit, False)
    existing_multireddits = [existing_multireddit['displayName'] for existing_multireddit in existing_multireddits]
    if not should_overwrite():
        return
    multireddits_uploaded_count = 0
    for multireddit in multireddits:
        if multireddit['displayName'] in existing_multireddits:
            print(f'Skipping multireddit {multireddit["displayName"]} as it already exists')
            skipped_resources['multireddits'].append(multireddit)
            continue
        reddit.multireddit.create(multireddit['displayName'], multireddit['subreddits'], visibility=multireddit['visibility'])
        multireddits_uploaded_count += 1
        print('Multireddits uploaded:', multireddits_uploaded_count)
    print('Total multireddits uploaded:', multireddits_uploaded_count)


def upload_subreddits_to_reddit(reddit, subreddits):
    """Upload subreddits to Reddit, skipping subreddits that are private or quarantined.
    
    Keyword arguments:
    reddit -- the PRAW Reddit instance
    subreddits -- the subreddits to upload to Reddit
    """
    print('\nUploading subreddits to Reddit')
    if not should_overwrite():
        return
    subreddit_model_list = []
    for subreddit in subreddits:
        if subreddit['isQuarantined']:
            print(f"Skipping subreddit {subreddit['displayName']} as it's quarantined")
        elif subreddit['subredditType'] != 'private':
            subreddit_model_list.append(reddit.subreddit(subreddit['displayName']))
            continue
        else:
            print(f"Skipping subreddit {subreddit['displayName']} as it's private")
        skipped_resources['subreddits'].append(subreddit)
    batched_subreddit_model_list = []
    subreddit_model_batch = []
    for subreddit_model in subreddit_model_list:
        subreddit_model_batch.append(subreddit_model)
        if len(subreddit_model_batch) == 1000:
            batched_subreddit_model_list.append(subreddit_model_batch)
            subreddit_model_batch = []
    if subreddit_model_batch:
        batched_subreddit_model_list.append(subreddit_model_batch)
    subreddits_uploaded_count = 0
    for subreddit_model_batch in batched_subreddit_model_list:
        reddit.subreddit(subreddit_model_batch[0].display_name).subscribe(other_subreddits=subreddit_model_batch[1:])
        subreddits_uploaded_count += len(subreddit_model_batch)
        print('Subreddits uploaded:', subreddits_uploaded_count)
        time.sleep(1)
    print('Total subreddits uploaded:', subreddits_uploaded_count)


def write_multireddits_to_file(multireddits):
    """Write multireddits to file.
    
    Keyword arguments:
    multireddits -- the multireddits to save to the file
    """
    dictionary = {
        'multireddits': multireddits
    }
    Path(DATA_DIRECTORY_NAME).mkdir(exist_ok=True, parents=True)
    if exists(multireddits_filename) and not should_overwrite(f'\n{multireddits_filename}{FILE_OVERWRITE_MESSAGE_SUFFIX}'):
        return
    with open(multireddits_filename, 'w') as f:
        json.dump(dictionary, f)


def write_skipped_resources_to_file():
    """Write skipped resources to file."""
    Path(DATA_DIRECTORY_NAME).mkdir(exist_ok=True, parents=True)
    if exists(multireddits_filename) and not should_overwrite(f'\n{skipped_resources_filename}{FILE_OVERWRITE_MESSAGE_SUFFIX}'):
        return
    with open(skipped_resources_filename, 'w') as f:
        json.dump(skipped_resources, f)
    print(f'Skipped resources were written to {skipped_resources_filename}')


def write_subreddits_to_file(subreddits):
    """Write subreddits to file.
    
    Keyword arguments:
    subreddits -- the subreddits to save to the file
    """
    dictionary = {
        'subreddits': subreddits
    }
    Path(DATA_DIRECTORY_NAME).mkdir(exist_ok=True, parents=True)
    if exists(multireddits_filename) and not should_overwrite(f'\n{subreddits_filename}{FILE_OVERWRITE_MESSAGE_SUFFIX}'):
        return
    with open(subreddits_filename, 'w') as f:
        json.dump(dictionary, f)


parser = argparse.ArgumentParser()
parser.add_argument('-d', '--download', action='store_true', help='Download data')
parser.add_argument('-u', '--upload', action='store_true', help='Upload data')
parser.add_argument('-o', '--overwrite', action='store_true', help='Overwrite data (local data or Reddit data) without confirming')
args = parser.parse_args()

skipped_resources = {
    'multireddits': [],
    'subreddits': [],
}

if args.download:
    print('Downloading data from Reddit')
    account_credentials = None
    if hasattr(config, 'DOWNLOAD_PASSWORD') and config.DOWNLOAD_PASSWORD and hasattr(config, 'DOWNLOAD_USERNAME') and config.DOWNLOAD_USERNAME:
        print(FOUND_ACCOUNT_CREDENTIALS_MESSAGE)
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
    write_multireddits_to_file(multireddits)
    subreddits = download_subreddits_from_reddit(reddit)
    write_subreddits_to_file(subreddits)

if args.upload:
    print_message_prepend_newline('Uploading data to Reddit', args.download)
    account_credentials = None
    if hasattr(config, 'UPLOAD_PASSWORD') and config.UPLOAD_PASSWORD and hasattr(config, 'UPLOAD_USERNAME') and config.UPLOAD_USERNAME:
        print(FOUND_ACCOUNT_CREDENTIALS_MESSAGE)
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
    upload_multireddits_to_reddit(multireddits, reddit)
    subreddits = get_subreddits_from_file()
    upload_subreddits_to_reddit(reddit, subreddits)
    write_skipped_resources_to_file()