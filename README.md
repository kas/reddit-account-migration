# reddit-account-migration
Migrate data from one Reddit account to another

## Usage
1. Clone the repo
1. Get a Reddit client ID and client secret for the Reddit account you're downloading from and for the Reddit account you're uploading to
   1. https://github.com/reddit-archive/reddit/wiki/OAuth2-Quick-Start-Example#first-steps
1. Paste your client IDs and client secrets in a new file named `config.py` in the root of the repo (DO NOT COMMIT THIS FILE)
1. **(Optional)** Provide the username and password for your Reddit accounts in the `config.py` file (DO NOT COMMIT THIS FILE)
1. Set up the venv: `python -m venv venv`
1. Enter the venv: `source venv/bin/activate`
1. Install the requirements: `pip install -r requirements.txt`
1. Run the script: `python main.py -d -u`
   1. -d and -u are the arguments most users would use, but see below to learn about all of the available arguments

Example `config.py` file (DO NOT COMMIT THIS FILE)
```
DOWNLOAD_CLIENT_ID = ''
DOWNLOAD_CLIENT_SECRET = ''

# Username and password are optional
DOWNLOAD_USERNAME = ''
DOWNLOAD_PASSWORD = ''

UPLOAD_CLIENT_ID = ''
UPLOAD_CLIENT_SECRET = ''

# Username and password are optional
UPLOAD_USERNAME = ''
UPLOAD_PASSWORD = ''
```

## Missing features
1. Saved resources (comments, submissions)
   1. There is support for downloading saved resources (see argument --include-saved-resources below [it's an opt-in argument]), but it takes forever to download all of them
   1. Support for uploading saved resources is still a to do because I'm not motivated to write the upload piece when download takes forever
   1. Migrating saved resources is not a priority in my opinion
   1. Beautiful Soup and Selenium might provide a solution for scraping saved resources in a quicker way

## Optional arguments
--download (-d)
- Download resources from Reddit (optionally using the DOWNLOAD username and password from the `config.py` file) and save the resources to files in the data directory
- Can be used with --upload (-u) and --skip arguments
```
python main.py -d
python main.py --download
```

--include-remindmebot-reminders (-ir)
- Include remindmebot reminder operations (to do)
- Can be used with --download (-d) and --upload (-u) and with other --skip arguments
- Downloading remindmebot reminders works fine, but uploading remindmebot reminders hasn't been successfully tested (that's why this argument is marked with to do). If you get an error (e.g., RESTRICTED_TO_PM) when trying to upload remindmebot reminders, then it's possible your Reddit account is too new to send messages to other users. Please try this function again when your Reddit account has higher karma.
```
python main.py -d -ir
python main.py -d --include-remindmebot-reminders
```

--include-saved-resources (-is)
- Include saved resource operations (to do)
- Can be used with --download (-d) and --upload (-u) and with other --skip arguments
```
python main.py -d -is
python main.py -d --include-saved-resources
```

--overwrite (-o)
- Overwrite data (local data or Reddit data) without confirming
- Can be used with --download (-d) and --upload (-u) and with other --skip arguments
```
python main.py -d -o
python main.py -d --overwrite
```

--skip-blocked-users (-sb)
- Skip blocked user operations
- Can be used with --download (-d) and --upload (-u) and with other --skip arguments
```
python main.py -d -sb
python main.py -d --skip-blocked-users
```

--skip-multireddits (-sm)
- Skip multireddit operations
- Can be used with --download (-d) and --upload (-u) and with other --skip arguments
```
python main.py -d -sm
python main.py -d --skip-multireddits
```

--skip-subreddits (-ss)
- Skip subreddit operations
- Can be used with --download (-d) and --upload (-u) and with other --skip arguments
```
python main.py -d -ss
python main.py -d --skip-subreddits
```

--upload (-u)
- Upload resources from the files in the data directory to Reddit (optionally using the UPLOAD username and password from the `config.py` file)
- Can be used with --download (-d) and --skip arguments
```
python main.py -u
python main.py --upload
```
