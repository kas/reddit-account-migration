import praw

from os.path import exists
from pathlib import Path
import argparse
import getpass
import json
import pprint
import sys

import config

# to do support multiple api creds, or see if you can just use a single set of api creds


def confirm_exists(filename):
    if not exists(filename):
        print(f'Error: {filename} doesn\'t exist. Exiting.')
        sys.exit()


def confirm_overwrite(filename):
    print(f'{filename} already exists. Do you want to overwrite it? (y/n)')
    user_input = input('> ')
    if user_input != 'y':
        print('Exiting')
        sys.exit()


def download_multis_from_reddit(reddit):
    multis = reddit.get('/api/multi/mine')
    multis_list = []
    for multi in multis:
        subreddits = []
        for subreddit in multi.subreddits:
            subreddits.append(subreddit.url)
        multis_list.append({
            'name': multi.name,
            'subreddits': subreddits,
        })
        print('Multis downloaded:', len(multis_list))
    print('Total multis downloaded:', len(multis_list))
    return multis_list


def download_subreddits_from_reddit(reddit):
    subreddits = reddit.get('/subreddits/mine/subscriber')
    subreddits_list = []
    while True:
        for subreddit in subreddits.children:
            if subreddits_list and subreddits_list[0] == subreddit.url:
                print('Total subreddits downloaded:', len(subreddits_list))
                return subreddits_list
            else:
                subreddits_list.append(subreddit.url)
        print('Subreddits downloaded:', len(subreddits_list))
        subreddits = reddit.get('/subreddits/mine/subscriber', params={ 'after': subreddits.after })


def get_multis_from_file():
    confirm_exists(multis_filename)
    with open(multis_filename) as f:
        dictionary = json.load(f)
        multis = dictionary['multis']
        return multis


def get_subreddits_from_file():
    confirm_exists(subreddits_filename)
    with open(subreddits_filename) as f:
        dictionary = json.load(f)
        subreddits = dictionary['subreddits']
        return subreddits


def get_account_information():
    print('Enter account information for download:')
    username = input('Username\n> ')
    print('Password\n> ', end='')
    password = getpass.getpass(prompt='')
    return (username, password)


def upload_subreddits_to_reddit(subreddits, reddit):
    # to do confirm before uploading
    subreddits_uploaded_count = 0
    for subreddit in subreddits:
        subreddit = subreddit.split('/')[-2]
        reddit.subreddit(subreddit).subscribe()
        subreddits_uploaded_count += 1
        print('Subreddits uploaded:', subreddits_uploaded_count)
    print('Total subreddits uploaded:', subreddits_uploaded_count)


def write_multis_to_file(multis, should_overwrite):
    dictionary = {
        'multis': multis
    }
    Path(data_directory_name).mkdir(exist_ok=True, parents=True)
    if not should_overwrite and exists(multis_filename):
        confirm_overwrite(filename)
    with open(filename, 'w') as f:
        json.dump(dictionary, f)


def write_subreddits_to_file(subreddits, should_overwrite):
    dictionary = {
        'subreddits': subreddits
    }
    Path(data_directory_name).mkdir(exist_ok=True, parents=True)
    if not should_overwrite and exists(subreddits_filename):
        confirm_overwrite(filename)
    with open(filename, 'w') as f:
        json.dump(dictionary, f)


data_directory_name = 'data'
multis_filename = f'{data_directory_name}/multis.json'
subreddits_filename = f'{data_directory_name}/subreddits.json'
user_agent = 'reddit-account-migration'

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
        user_agent=user_agent,
        # username=account_information[0],
        username=config.username,
    )
    # multis = download_multis_from_reddit(reddit)
    # write_multis_to_file(multis, args.overwrite)
    # subreddits = download_subreddits_from_reddit(reddit)
    # write_subreddits_to_file(subreddits, args.overwrite)

if args.upload:
    # account_information = get_account_information()
    reddit = praw.Reddit(
        client_id=config.client_id,
        client_secret=config.client_secret,
        # password=account_information[1],
        password=config.password,
        user_agent=user_agent,
        # username=account_information[0],
        username=config.username,
    )
    # multis = get_multis_from_file()
    # upload_multis_to_reddit(multis, reddit)
    subreddits = get_subreddits_from_file()
    upload_subreddits_to_reddit(subreddits, reddit)