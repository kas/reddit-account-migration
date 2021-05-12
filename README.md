# reddit-account-migration
## How to use
1. Clone the repository
1. [Get a Reddit client ID and client secret for the account you're downloading from and for the account you're uploading to](https://github.com/reddit-archive/reddit/wiki/OAuth2-Quick-Start-Example#first-steps)
1. Paste your client IDs and client secrets in a new file named config.py in the root of the repository (DO NOT COMMIT THIS FILE)
1. Optionally put your account credentials in the config.py file (DO NOT COMMIT THIS FILE)
1. Set up the venv: `py -m venv venv`
1. Enter the venv: `.\venv\Scripts\Activate.ps1`
1. Install the requirements: `pip install -r requirements.txt`
1. Run the script: `py main.py -d -u`

Example config.py (DO NOT COMMIT THIS FILE)
```
DOWNLOAD_CLIENT_ID = ''
DOWNLOAD_CLIENT_SECRET = ''

DOWNLOAD_PASSWORD = ''
DOWNLOAD_USERNAME = ''

UPLOAD_CLIENT_ID = ''
UPLOAD_CLIENT_SECRET = ''

UPLOAD_PASSWORD = ''
UPLOAD_USERNAME = ''
```
## Optional arguments
--download (-d)
- Download resources from Reddit (optionally using the DOWNLOAD username and password from the config.py file) and save the resources to files in the data directory
- Can be used with --upload (-u) and --exclude arguments
```
py main.py -d
py main.py --download
```

--upload (-u)
- Upload resources from the files in the data directory to Reddit (optionally using the UPLOAD username and password from the config.py file)
- Can be used with --download (-d) and --exclude arguments
```
py main.py -u
py main.py --upload
```

--exclude-blocked-users (-eb)
- Skip blocked user operations
- Can be used with --download (-d) and --upload (-u) and with other --exclude arguments
```
py main.py -d -eb
py main.py -d --exclude-blocked-users
```

--exclude-multireddits (-em)
- Skip multireddit operations
- Can be used with --download (-d) and --upload (-u) and with other --exclude arguments
```
py main.py -d -em
py main.py -d --exclude-multireddits
```

--exclude-subreddits (-es)
- Skip subreddit operations
- Can be used with --download (-d) and --upload (-u) and with other --exclude arguments
```
py main.py -d -es
py main.py -d --exclude-subreddits
```

--overwrite (-o)
- Overwrite data (local data or Reddit data) without confirming
- Can be used with --download (-d) and --upload (-u) and with other --exclude arguments
```
py main.py -d -o
py main.py -d --overwrite
```