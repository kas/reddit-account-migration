import praw

from os.path import exists
from pathlib import Path
import argparse
import getpass
import json
import sys

import config


def confirm_overwrite(filename):
    print(f'{filename} already exists. Do you want to overwrite it? (y/n)')
    user_input = input('> ')
    if user_input != 'y':
        print('Exiting')
        sys.exit()


def get_subreddits(reddit):
    subreddits = reddit.get('/subreddits/mine/subscriber')
    subreddits_list = []
    while True:
        for subreddit in subreddits.children:
            if subreddits_list and subreddits_list[0] == subreddit.url:
                print('Total subreddits retrieved:', len(subreddits_list))
                return subreddits_list
            else:
                subreddits_list.append(subreddit.url)
        print('Subreddits retrieved:', len(subreddits_list))
        subreddits = reddit.get('/subreddits/mine/subscriber', params={ 'after': subreddits.after })


def get_account_information():
    print('Enter account information for export:')
    username = input('Username\n> ')
    print('Password\n> ', end='')
    password = getpass.getpass(prompt='')
    return (username, password)


def write_subreddits_to_file(subreddits, should_overwrite):
    dictionary = {
        'subreddits': subreddits
    }
    Path(data_directory_name).mkdir(exist_ok=True, parents=True)
    filename = f'{data_directory_name}/subreddits.json'
    if not should_overwrite and exists(filename):
        confirm_overwrite(filename)
    with open(filename, 'w') as f:
        json.dump(dictionary, f)


data_directory_name = 'data'
user_agent = 'reddit-account-migration'

parser = argparse.ArgumentParser()
parser.add_argument('-e', '--export', action='store_true')
parser.add_argument('-i', '--import', action='store_true')
parser.add_argument('-o', '--overwrite', action='store_true', help='Overwrite files without confirming')
args = parser.parse_args()

if args.export:
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
    subreddits = get_subreddits(reddit)
    write_subreddits_to_file(subreddits, args.overwrite)

    # get my multireddits
    # https://www.reddit.com/dev/api#GET_api_multi_mine