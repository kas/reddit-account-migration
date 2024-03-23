from os.path import exists
from pathlib import Path
import argparse
import datetime
import getpass
import json
import sys
import time

from praw.models import Comment, Submission
import praw
import prawcore

import config

BLOCKED_USERS_KEY = 'blockedUsers'
DATA_DIRECTORY_NAME = 'data'
DATETIME_KEY = 'datetime'
DISPLAY_NAME_KEY = 'displayName'
DOWNLOAD_PASSWORD_VARIABLE_NAME = 'DOWNLOAD_PASSWORD'
DOWNLOAD_USERNAME_VARIABLE_NAME = 'DOWNLOAD_USERNAME'
FOUND_ACCOUNT_CREDENTIALS_MESSAGE = 'Found Reddit account credentials from config.py'
GET_ACCOUNT_CREDENTIALS_MESSAGE_PREFIX = '\nEnter Reddit account credentials for '
IS_QUARANTINED_KEY = 'isQuarantined'
MULTIREDDITS_KEY = 'multireddits'
REMINDMEBOT_MESSAGE_BODY = 'MyReminders!'
REMINDMEBOT_MESSAGE_SUBJECT = 'RemindMe'
REMINDMEBOT_REMINDERS_KEY = 'remindmebotReminders'
REMINDMEBOT_USERNAME = 'RemindMeBot'
SAVED_RESOURCES_KEY = 'savedResources'
SOURCE_KEY = 'source'
SUBREDDIT_TYPE_KEY = 'subredditType'
SUBREDDITS_KEY = 'subreddits'
UPLOAD_PASSWORD_VARIABLE_NAME = 'UPLOAD_PASSWORD'
UPLOAD_USERNAME_VARIABLE_NAME = 'UPLOAD_USERNAME'
USER_AGENT = 'reddit-account-migration'
VISIBILITY_KEY = 'visibility'
WAITING_TO_CHECK_REDDIT_INBOX_MESSAGE = 'Waiting 10 seconds to check Reddit inbox'

BLOCKED_USERS_FILENAME = f'{DATA_DIRECTORY_NAME}/blocked-users.json'
GET_ACCOUNT_CREDENTIALS_MESSAGE_DOWNLOAD = f'{GET_ACCOUNT_CREDENTIALS_MESSAGE_PREFIX}download:'
GET_ACCOUNT_CREDENTIALS_MESSAGE_UPLOAD = f'{GET_ACCOUNT_CREDENTIALS_MESSAGE_PREFIX}upload:'
MULTIREDDITS_FILENAME = f'{DATA_DIRECTORY_NAME}/multireddits.json'
REMINDMEBOT_REMINDERS_FILENAME = f'{DATA_DIRECTORY_NAME}/remindmebot-reminders.json'
SAVED_RESOURCES_FILENAME = f'{DATA_DIRECTORY_NAME}/saved-resources.json'
SKIPPED_RESOURCES_FILENAME = f'{DATA_DIRECTORY_NAME}/skipped-resources.json'
SUBREDDITS_FILENAME = f'{DATA_DIRECTORY_NAME}/subreddits.json'


def download_remindmebot_reminders_from_reddit(reddit):
    """Download remindmebot reminders from Reddit and return them.
    
    Keyword arguments:
    reddit -- the PRAW Reddit instance
    """
    print('\nDownloading remindmebot reminders from Reddit')
    remindmebot_reminders = []
    message_sent_timestamp = datetime.datetime.now().timestamp()
    print('Messaging RemindMeBot to get current reminders')
    reddit.redditor(REMINDMEBOT_USERNAME).message(REMINDMEBOT_MESSAGE_SUBJECT, REMINDMEBOT_MESSAGE_BODY)
    print(WAITING_TO_CHECK_REDDIT_INBOX_MESSAGE)
    remindmebot_message = None
    while not remindmebot_message:
        time.sleep(10)
        print('Checking Reddit inbox for reply from RemindMeBot')
        messages = reddit.inbox.messages(limit=None)
        for message in messages:
            if message.author and message.author.name == reddit.user.me().name and message.body == REMINDMEBOT_MESSAGE_BODY and message.subject == REMINDMEBOT_MESSAGE_SUBJECT and message.created_utc >= message_sent_timestamp and message.replies:
                remindmebot_message = message.replies[0].body
                break
            elif message.created_utc < message_sent_timestamp:
                print("Didn't find reply from RemindMeBot")
                break
        print(f'{WAITING_TO_CHECK_REDDIT_INBOX_MESSAGE} again')
    for line in remindmebot_message.split('\n'):
        if line.startswith('|[Source](https://'):
            line_segments = line.split('|')
            source = line_segments[2] if line_segments[2] else line_segments[1].split('(')[-1].replace(')', '')
            reminder_datetime = line_segments[3].split('**')[1]
            remindmebot_reminders.append({
                DATETIME_KEY: reminder_datetime,
                SOURCE_KEY: source,
            })
    print('Total remindmebot reminders downloaded:', len(remindmebot_reminders))
    return remindmebot_reminders


def download_blocked_users_from_reddit(reddit):
    """Download blocked users from Reddit and return them.
    
    Keyword arguments:
    reddit -- the PRAW Reddit instance
    """
    print('\nDownloading blocked users from Reddit')
    blocked_users = [blocked_user.name for blocked_user in reddit.user.blocked()]
    print('Total blocked users downloaded:', len(blocked_users))
    return blocked_users
 

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
            DISPLAY_NAME_KEY: multireddit.display_name,
            SUBREDDITS_KEY: subreddits,
            VISIBILITY_KEY: multireddit.visibility,
        })
        print('Multireddits downloaded:', len(multireddits_list))
    print('Total multireddits downloaded:', len(multireddits_list))
    return multireddits_list


def download_saved_resources_from_reddit(reddit):
    """Download saved resources from Reddit and return them.
    
    Keyword arguments:
    reddit -- the PRAW Reddit instance
    """
    print('\nDownloading saved resources from Reddit')
    saved_resources = reddit.user.me().saved(limit=None)
    saved_resources_list = []
    for saved_resource in saved_resources:
        saved_resource_type = None
        if isinstance(saved_resource, Comment):
            saved_resource_type = 'comment'
        elif isinstance(saved_resource, Submission):
            saved_resource_type = 'submission'
        else:
            print('\n\n\nERROR new saved resource type')
            print(saved_resource)
            continue
        saved_resources_list.append({
            'authorName': saved_resource.author if not saved_resource.author else saved_resource.author.name,
            'permalink': saved_resource.permalink,
            'savedResourceType': saved_resource_type,
            'title': saved_resource.title if not hasattr(saved_resource, 'submission') else saved_resource.submission.title,
        })
        print('Saved resources downloaded:', len(saved_resources_list))
    print('Total saved resources downloaded:', len(saved_resources_list))
    return saved_resources_list


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
            DISPLAY_NAME_KEY: subreddit.display_name,
            IS_QUARANTINED_KEY: subreddit.quarantine,
            SUBREDDIT_TYPE_KEY: subreddit.subreddit_type,
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


def get_dictionary(key, resources):
    """Return a new dictionary using the given key and resources (key value).

    Keyword arguments:
    key -- the key to use in the dictionary
    resources -- the resources to use as the key value
    """
    return {
        key: resources,
    }


def get_from_file(filename, key):
    """Get the resource from the filename and return it.
    
    Keyword arguments:
    filename -- the filename
    key -- the key of the resource
    """
    if not exists(filename):
        exit_script(f"Error: {filename} doesn't exist. Exiting.")
    with open(filename) as f:
        dictionary = json.load(f)
        resource = dictionary[key]
        return resource


def get_password():
    """Prompt the user to enter their Reddit account password and return it."""
    print('Password\n> ', end='')
    password = getpass.getpass(prompt='')
    print('Confirm password\n> ', end='')
    confirm_password = getpass.getpass(prompt='')
    return (confirm_password, password)


def get_reddit(account_credentials, client_id, client_secret, message):
    """Get the PRAW Reddit instance, allowing the user to enter their Reddit account credentials again if authentication fails.
    
    Keyword arguments:
    account_credentials -- the Reddit account credentials
    client_id -- the client ID for the Reddit app
    client_secret -- the client secret for the Reddit app
    message -- the message to prompt the user with if authentication fails
    """
    while True:
        try:
            reddit = praw.Reddit(
                client_id=client_id,
                client_secret=client_secret,
                password=account_credentials[0],
                user_agent=USER_AGENT,
                username=account_credentials[1],
            )
            reddit.user.me()
            return reddit
        except prawcore.OAuthException:
            print('\nError: Authentication failed. Would you like to try entering your Reddit account credentials again? (y/n)')
            user_input = input('> ')
            if user_input == 'n':
                exit_script()
            account_credentials = get_account_credentials(message)


def print_message_prepend_newline(message, should_prepend_newline=True):
    """Print a message prepended by a newline.
    
    Keyword arguments:
    message -- the message to print
    should_prepend_newline -- whether or not to prepend the message with a newline (default True)
    """
    message = f'\n{message}' if should_prepend_newline else message
    print(message)


def should_overwrite(message='\nDo you want to upload this data to your Reddit account?', reddit=None):
    """Return whether or not the resource should be overwritten.
    
    Keyword arguments:
    message -- the message to prompt the user with (default Reddit overwrite message string)
    reddit -- the PRAW Reddit instance (default None)
    """
    if not args.overwrite:
        print(message)
        if reddit:
            print('Reddit account:', reddit.user.me().name)
        user_input = input('(y/n)\n> ')
        return user_input == 'y'
    return True


def upload_blocked_users_to_reddit(blocked_users, reddit):
    """Upload blocked users to Reddit.
    
    Keyword arguments:
    blocked_users -- the blocked users to upload to Reddit
    reddit -- the PRAW Reddit instance
    """
    print('\nUploading blocked users to Reddit')
    if not should_overwrite(reddit=reddit):
        return
    blocked_users_uploaded_count = 0
    for blocked_user in blocked_users:
        reddit.redditor(blocked_user).block()
        blocked_users_uploaded_count += 1
        print('Blocked users uploaded:', blocked_users_uploaded_count)
    print('Total blocked users uploaded:', blocked_users_uploaded_count)


def upload_multireddits_to_reddit(multireddits, reddit):
    """Upload multireddits to Reddit, skipping any multireddit that already exists.
    
    Keyword arguments:
    multireddits -- the multireddits to upload to Reddit
    reddit -- the PRAW Reddit instance
    """
    print('\nUploading multireddits to Reddit')
    print('Downloading existing multireddits to prevent collisions')
    existing_multireddits = download_multireddits_from_reddit(reddit, False)
    existing_multireddits = [existing_multireddit[DISPLAY_NAME_KEY] for existing_multireddit in existing_multireddits]
    if not should_overwrite(reddit=reddit):
        return
    multireddits_uploaded_count = 0
    for multireddit in multireddits:
        if multireddit[DISPLAY_NAME_KEY] in existing_multireddits:
            print(f'Skipping multireddit {multireddit[DISPLAY_NAME_KEY]} as it already exists')
            skipped_resources[MULTIREDDITS_KEY].append(multireddit)
            continue
        reddit.multireddit.create(multireddit[DISPLAY_NAME_KEY], multireddit[SUBREDDITS_KEY], visibility=multireddit[VISIBILITY_KEY])
        multireddits_uploaded_count += 1
        print('Multireddits uploaded:', multireddits_uploaded_count)
    print('Total multireddits uploaded:', multireddits_uploaded_count)


def upload_remindmebot_reminders_to_reddit(reddit, remindmebot_reminders):
    """Upload remindmebot reminders to Reddit.
    
    Keyword arguments:
    reddit -- the PRAW Reddit instance
    remindmebot_reminders -- the remindmebot reminders to upload to Reddit
    """
    print('\nUploading remindmebot reminders to Reddit')
    if not should_overwrite(reddit=reddit):
        return
    remindmebot_reminders_uploaded_count = 0
    error_encountered = False
    for remindmebot_reminder in [remindmebot_reminders[0]]:
        try:
            reddit.redditor(REMINDMEBOT_USERNAME).message(REMINDMEBOT_MESSAGE_SUBJECT, f'RemindMe! {remindmebot_reminder[DATETIME_KEY]} "{remindmebot_reminder[SOURCE_KEY]}"')
            remindmebot_reminders_uploaded_count += 1
        except praw.exceptions.RedditAPIException as exception:
            error_encountered = True
            skipped_resources[REMINDMEBOT_REMINDERS_KEY].append(remindmebot_reminder)
            for subexception in exception.items:
                print(f'\nException: {subexception.error_type}')
            print("\nError: RedditAPIException. If the error above is about RESTRICTED_TO_PM, it's possible your Reddit account is too new to send messages to other users. Please try this function again when your Reddit account has higher karma.")
        print_message_prepend_newline(f'Remindmebot reminders uploaded: {remindmebot_reminders_uploaded_count}', error_encountered)
    print('Total remindmebot reminders uploaded:', remindmebot_reminders_uploaded_count)


def upload_subreddits_to_reddit(reddit, subreddits):
    """Upload subreddits to Reddit, skipping subreddits that are private or quarantined.
    
    Keyword arguments:
    reddit -- the PRAW Reddit instance
    subreddits -- the subreddits to upload to Reddit
    """
    print('\nUploading subreddits to Reddit')
    if not should_overwrite(reddit=reddit):
        return
    subreddit_model_list = []
    for subreddit in subreddits:
        if subreddit[IS_QUARANTINED_KEY]:
            print(f"Skipping subreddit {subreddit[DISPLAY_NAME_KEY]} as it's quarantined")
        elif subreddit[SUBREDDIT_TYPE_KEY] != 'private':
            subreddit_model_list.append(reddit.subreddit(subreddit[DISPLAY_NAME_KEY]))
            continue
        else:
            print(f"Skipping subreddit {subreddit[DISPLAY_NAME_KEY]} as it's private")
        skipped_resources[SUBREDDITS_KEY].append(subreddit)
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
        time.sleep(10)
    print('Total subreddits uploaded:', subreddits_uploaded_count)

def upload_saved_resources_to_reddit(reddit, saved_resources):
    """Upload saved resources to Reddit.
    
    Keyword arguments:
    reddit -- the PRAW Reddit instance
    saved_resources -- the saved resources to upload to Reddit
    """
    print('\nUploading saved resources to Reddit')
    "Reverse the list so that the sorting will be preserved"
    saved_resources.reverse()
    saved_resources_uploaded_count = 0
    for resource in saved_resources:
        if resource['savedResourceType'] == 'submission':
            reddit.submission(url='https://reddit.com' + resource['permalink']).save()
        elif resource['savedResourceType'] == 'comment':
            reddit.comment(url='https://reddit.com' + resource['permalink']).save()
        saved_resources_uploaded_count += 1
        print('Saved resources uploaded:', saved_resources_uploaded_count)
    print('Total saved resources uploaded:', saved_resources_uploaded_count)

def write_skipped_resources_to_file():
    """Write skipped resources to file."""
    write_to_file(skipped_resources, SKIPPED_RESOURCES_FILENAME)
    print(f'Skipped resources were written to {SKIPPED_RESOURCES_FILENAME}')


def write_to_file(dictionary, filename):
    """Write the dictionary to the filename.
    
    Keyword arguments:
    dictionary -- the dictionary to write
    filename -- the filename
    """
    Path(DATA_DIRECTORY_NAME).mkdir(exist_ok=True, parents=True)
    if exists(filename) and not should_overwrite(f'\n{filename} already exists. Do you want to overwrite it?'):
        return
    with open(filename, 'w') as f:
        json.dump(dictionary, f)


parser = argparse.ArgumentParser()
parser.add_argument('-d', '--download', action='store_true', help='Download resources from Reddit and save the resources to files in the data directory')
parser.add_argument('-ir', '--include-remindmebot-reminders', action='store_true', help='Include remindmebot reminder operations (to do)')
parser.add_argument('-is', '--include-saved-resources', action='store_true', help='Include saved resource operations (to do)')
parser.add_argument('-o', '--overwrite', action='store_true', help='Overwrite data (local data or Reddit data) without confirming')
parser.add_argument('-sb', '--skip-blocked-users', action='store_true', help='Skip blocked user operations')
parser.add_argument('-sm', '--skip-multireddits', action='store_true', help='Skip multireddit operations')
parser.add_argument('-ss', '--skip-subreddits', action='store_true', help='Skip subreddit operations')
parser.add_argument('-u', '--upload', action='store_true', help='Upload resources from the files in the data directory to Reddit')
args = parser.parse_args()

skipped_resources = {
    MULTIREDDITS_KEY: [],
    REMINDMEBOT_REMINDERS_KEY: [],
    SUBREDDITS_KEY: [],
}

if args.download:
    print('Downloading data from Reddit')
    account_credentials = None
    if hasattr(config, DOWNLOAD_PASSWORD_VARIABLE_NAME) and config.DOWNLOAD_PASSWORD and hasattr(config, DOWNLOAD_USERNAME_VARIABLE_NAME) and config.DOWNLOAD_USERNAME:
        print(FOUND_ACCOUNT_CREDENTIALS_MESSAGE)
        account_credentials = (config.DOWNLOAD_PASSWORD, config.DOWNLOAD_USERNAME)
    else:
        account_credentials = get_account_credentials(GET_ACCOUNT_CREDENTIALS_MESSAGE_DOWNLOAD)
    reddit = get_reddit(account_credentials, config.DOWNLOAD_CLIENT_ID, config.DOWNLOAD_CLIENT_SECRET, GET_ACCOUNT_CREDENTIALS_MESSAGE_DOWNLOAD)
    if args.include_remindmebot_reminders:
        remindmebot_reminders = download_remindmebot_reminders_from_reddit(reddit)
        write_to_file(get_dictionary(REMINDMEBOT_REMINDERS_KEY, remindmebot_reminders), REMINDMEBOT_REMINDERS_FILENAME)
    if args.include_saved_resources:
        saved_resources = download_saved_resources_from_reddit(reddit)
        write_to_file(get_dictionary(SAVED_RESOURCES_KEY, saved_resources), SAVED_RESOURCES_FILENAME)
    if not args.skip_blocked_users:
        blocked_users = download_blocked_users_from_reddit(reddit)
        write_to_file(get_dictionary(BLOCKED_USERS_KEY, blocked_users), BLOCKED_USERS_FILENAME)
    if not args.skip_multireddits:
        multireddits = download_multireddits_from_reddit(reddit)
        write_to_file(get_dictionary(MULTIREDDITS_KEY, multireddits), MULTIREDDITS_FILENAME)
    if not args.skip_subreddits:
        subreddits = download_subreddits_from_reddit(reddit)
        write_to_file(get_dictionary(SUBREDDITS_KEY, subreddits), SUBREDDITS_FILENAME)

if args.upload:
    print_message_prepend_newline('Uploading data to Reddit', args.download)
    account_credentials = None
    if hasattr(config, UPLOAD_PASSWORD_VARIABLE_NAME) and config.UPLOAD_PASSWORD and hasattr(config, UPLOAD_USERNAME_VARIABLE_NAME) and config.UPLOAD_USERNAME:
        print(FOUND_ACCOUNT_CREDENTIALS_MESSAGE)
        account_credentials = (config.UPLOAD_PASSWORD, config.UPLOAD_USERNAME)
    else:
        account_credentials = get_account_credentials(GET_ACCOUNT_CREDENTIALS_MESSAGE_UPLOAD)
    reddit = get_reddit(account_credentials, config.UPLOAD_CLIENT_ID, config.UPLOAD_CLIENT_SECRET, GET_ACCOUNT_CREDENTIALS_MESSAGE_UPLOAD)
    if args.include_remindmebot_reminders:
        remindmebot_reminders = get_from_file(REMINDMEBOT_REMINDERS_FILENAME, REMINDMEBOT_REMINDERS_KEY)
        upload_remindmebot_reminders_to_reddit(reddit, remindmebot_reminders)
    if args.include_saved_resources:
        saved_resources = get_from_file(SAVED_RESOURCES_FILENAME, SAVED_RESOURCES_KEY)
        upload_saved_resources_to_reddit(reddit, saved_resources)
    if not args.skip_blocked_users:
        blocked_users = get_from_file(BLOCKED_USERS_FILENAME, BLOCKED_USERS_KEY)
        upload_blocked_users_to_reddit(blocked_users, reddit)
    if not args.skip_multireddits:
        multireddits = get_from_file(MULTIREDDITS_FILENAME, MULTIREDDITS_KEY)
        upload_multireddits_to_reddit(multireddits, reddit)
    if not args.skip_subreddits:
        subreddits = get_from_file(SUBREDDITS_FILENAME, SUBREDDITS_KEY)
        upload_subreddits_to_reddit(reddit, subreddits)
    write_skipped_resources_to_file()
