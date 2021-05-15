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
   1. -d and -u are the arguments most users would use, but see below to learn about all of the available arguments

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
## Missing features
1. Saved resources (comments, submissions)
   1. There is support for downloading saved resources (see argument --include-saved-resources below [it's an opt-in argument]), but it takes forever to download all of them
   1. Support for uploading saved resources is still a to do because I'm not motivated to write the upload piece when download takes forever
   1. Migrating saved resources is not a priority in my opinion
   1. Beautiful Soup and Selenium might provide a solution for scraping saved resources in a quicker way
## Optional arguments
--download (-d)
- Download resources from Reddit (optionally using the DOWNLOAD username and password from the config.py file) and save the resources to files in the data directory
- Can be used with --upload (-u) and --skip arguments
```
py main.py -d
py main.py --download
```

--include-saved-resources (-isr)
- Include saved resource operations (to do)
- Can be used with --download (-d) and --upload (-u) and with other --skip arguments
```
py main.py -d -isr
py main.py -d --include-saved-resources
```

--overwrite (-o)
- Overwrite data (local data or Reddit data) without confirming
- Can be used with --download (-d) and --upload (-u) and with other --skip arguments
```
py main.py -d -o
py main.py -d --overwrite
```

--skip-blocked-users (-sb)
- Skip blocked user operations
- Can be used with --download (-d) and --upload (-u) and with other --skip arguments
```
py main.py -d -sb
py main.py -d --skip-blocked-users
```

--skip-multireddits (-sm)
- Skip multireddit operations
- Can be used with --download (-d) and --upload (-u) and with other --skip arguments
```
py main.py -d -sm
py main.py -d --skip-multireddits
```

--skip-subreddits (-ss)
- Skip subreddit operations
- Can be used with --download (-d) and --upload (-u) and with other --skip arguments
```
py main.py -d -ss
py main.py -d --skip-subreddits
```

--upload (-u)
- Upload resources from the files in the data directory to Reddit (optionally using the UPLOAD username and password from the config.py file)
- Can be used with --download (-d) and --skip arguments
```
py main.py -u
py main.py --upload
```