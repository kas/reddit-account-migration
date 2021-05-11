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