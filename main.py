from os.path import exists
from pathlib import Path
import argparse
import getpass
import json
import pprint
import sys

import praw

import config

# to do normalize Reddit interactions (either API, PRAW API, or praw)
# to do support multiple api creds, or see if you can just use a single set of api creds

DATA_DIRECTORY_NAME = 'data'
FILE_OVERWRITE_MESSAGE_SUFFIX = ' already exists. Do you want to overwrite it?'
REDDIT_OVERWRITE_MESSAGE = 'Do you want to upload this data to your Reddit account?'
USER_AGENT = 'reddit-account-migration'

multis_filename = f'{DATA_DIRECTORY_NAME}/multis.json'
subreddits_filename = f'{DATA_DIRECTORY_NAME}/subreddits.json'


def confirm_exists(filename):
    '''If the filename doesn't exist then print an error message and exit'''
    if not exists(filename):
        print(f'Error: {filename} doesn\'t exist. Exiting.')
        sys.exit()


def confirm_overwrite(message):
    '''Prompt the user to confirm if the resource should be overwritten and exit if not'''
    print(message)
    user_input = input('(y/n)\n> ')
    if user_input != 'y':
        print('Exiting')
        sys.exit()


def download_multis_from_reddit(reddit):
    '''Download multis from Reddit and return them'''
    print('Downloading multis from Reddit')
    multis = reddit.get('/api/multi/mine')
    multis_list = []
    for multi in multis:
        subreddits = []
        for subreddit in multi.subreddits:
            subreddits.append(get_subreddit_from_url(subreddit.url))
        multis_list.append({
            'displayName': multi.display_name,
            'name': multi.name,
            'subreddits': subreddits,
            'visibility': multi.visibility,
        })
        print('Multis downloaded:', len(multis_list))
    print('Total multis downloaded:', len(multis_list))
    return multis_list


def download_subreddits_from_reddit(reddit):
    '''Download subreddits from Reddit and return them'''
    print('Downloading subreddits from Reddit')
    subreddits = reddit.get('/subreddits/mine/subscriber')
    subreddits_list = []
    while True:
        for subreddit in subreddits.children:
            if subreddits_list and subreddits_list[0] == subreddit.url:
                print('Total subreddits downloaded:', len(subreddits_list))
                return subreddits_list
            else:
                subreddits_list.append(get_subreddit_from_url(subreddit.url))
        print('Subreddits downloaded:', len(subreddits_list))
        subreddits = reddit.get('/subreddits/mine/subscriber', params={ 'after': subreddits.after })


def get_multis_from_file():
    '''Get multis from file and return them'''
    confirm_exists(multis_filename)
    with open(multis_filename) as f:
        dictionary = json.load(f)
        multis = dictionary['multis']
        return multis


def get_subreddit_from_url(subreddit):
    return subreddit.split('/')[-2]


def get_subreddits_from_file():
    '''Get subreddits from file and return them'''
    confirm_exists(subreddits_filename)
    with open(subreddits_filename) as f:
        dictionary = json.load(f)
        subreddits = dictionary['subreddits']
        return subreddits


def get_account_credentials():
    '''Prompt the user to enter their Reddit account credentials and return them'''
    print('Enter account information for download:')
    username = input('Username\n> ')
    print('Password\n> ', end='')
    password = getpass.getpass(prompt='')
    return (username, password)


def upload_multis_to_reddit(multis, reddit, should_overwrite):
    '''Upload multis to Reddit'''
    print('Uploading multis to Reddit')
    if not should_overwrite:
        confirm_overwrite(REDDIT_OVERWRITE_MESSAGE)
    multis_uploaded_count = 0
    for multi in multis:
        # create the multi
        reddit.multireddit.create('testingss', 'Games')
        break # debug
        for subreddit in multi['subreddits']:
            # add the subreddit to the multi
            print(subreddit)
        multis_uploaded_count += 1
        print('Multis uploaded:', multis_uploaded_count)
    print('Total multis uploaded:', multis_uploaded_count)


def upload_subreddits_to_reddit(subreddits, reddit, should_overwrite):
    '''Upload subreddits to Reddit'''
    print('Uploading subreddits to Reddit')
    if not should_overwrite:
        confirm_overwrite(REDDIT_OVERWRITE_MESSAGE)
    subreddits_uploaded_count = 0
    for subreddit in subreddits:
        reddit.subreddit(subreddit).subscribe()
        subreddits_uploaded_count += 1
        print('Subreddits uploaded:', subreddits_uploaded_count)
    print('Total subreddits uploaded:', subreddits_uploaded_count)


def write_multis_to_file(multis, should_overwrite):
    '''Write multis to file'''
    dictionary = {
        'multis': multis
    }
    Path(DATA_DIRECTORY_NAME).mkdir(exist_ok=True, parents=True)
    if not should_overwrite and exists(multis_filename):
        confirm_overwrite(f'{multis_filename}{FILE_OVERWRITE_MESSAGE_SUFFIX}')
    with open(multis_filename, 'w') as f:
        json.dump(dictionary, f)


def write_subreddits_to_file(subreddits, should_overwrite):
    '''Write subreddits to file'''
    dictionary = {
        'subreddits': subreddits
    }
    Path(DATA_DIRECTORY_NAME).mkdir(exist_ok=True, parents=True)
    if not should_overwrite and exists(subreddits_filename):
        confirm_overwrite(f'{subreddits_filename}{FILE_OVERWRITE_MESSAGE_SUFFIX}')
    with open(filename, 'w') as f:
        json.dump(dictionary, f)


parser = argparse.ArgumentParser()
parser.add_argument('-d', '--download', action='store_true', help='Download data')
parser.add_argument('-u', '--upload', action='store_true', help='Upload data')
parser.add_argument('-o', '--overwrite', action='store_true', help='Overwrite data (local data or Reddit data) without confirming')
args = parser.parse_args()

if args.download:
    # account_information = get_account_information()
    # to do deduplicate praw.Reddit call
    reddit = praw.Reddit(
        client_id=config.client_id,
        client_secret=config.client_secret,
        # password=account_information[1],
        password=config.password,
        user_agent=USER_AGENT,
        # username=account_information[0],
        username=config.username,
    )
    multis = download_multis_from_reddit(reddit)
    write_multis_to_file(multis, args.overwrite)
    subreddits = download_subreddits_from_reddit(reddit)
    write_subreddits_to_file(subreddits, args.overwrite)

if args.upload:
    # account_information = get_account_information()
    reddit = praw.Reddit(
        client_id=config.client_id,
        client_secret=config.client_secret,
        # password=account_information[1],
        password=config.password,
        user_agent=USER_AGENT,
        # username=account_information[0],
        username=config.username,
    )
    multis = get_multis_from_file()
    upload_multis_to_reddit(multis, reddit, args.overwrite)
    # subreddits = get_subreddits_from_file()
    # upload_subreddits_to_reddit(subreddits, reddit, args.overwrite)