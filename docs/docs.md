### Setup

To deploy this scraper you need to fork this repository.

### Twitter Credentials:
You need to have a Twitter account and provide your credentials to the scraper.

❗️❗️To scrape Twitter you need session file, it can be created by running `twitter_sign_in.py` **locally**❗️❗️

Or for example https://github.dev/. 

I use `poetry` for dependency management, so you need to install it first.
After that, run `poetry shell` and `poetry install` to install all dependencies.
Then run `poetry run python twitter_sign_in.py` and follow the instructions.

### GitHub Actions:

#### Add Twitter Credentials 
Then navigate to your repository on GitHub, click on "Settings", then "Secrets", and finally "Actions". Click on "New repository secret" to add a new secret. Provide a name for your secret (`TWITTER_USERNAME` and `TWITTER_PASSWORD`) and the corresponding values, then click "Add secret".

#### Enable Write Access    
You need to enable write access to the repository.
Go to your repository on GitHub, click on "Settings", then "Actions", "General" and at "Workflow permissions" enable "Read and write permissions".

![image](docs/gh_action.jpg)

### Firestore Setup:
Notice:
There is `cloudfree` branch, that generates scrapes and saves them to `json` files, without using Cloud Database.

#### GCloud Setup:
You need to have Google Cloud account.
1. Create a Google Cloud Project
- Go to the Google Cloud Console.
- Click the project drop-down and select or create the project for which you want to add an API key.
- Click the hamburger menu in the top left corner and select "APIs & Services" > "Dashboard".
- Click "Create Project" if you're starting from scratch, or select an existing project if you already have one.
2. Enable Firestore API
- In the Google Cloud Console, go to the "APIs & Services" > "Library" section.
- Search for "Cloud Firestore API" and click on it.
- Click "Enable" to enable the Firestore API for your project.
3. Create a Firestore Database
- In the Google Cloud Console, go to the "Firestore Database" section.
- Click "Create database".
- Choose "Start in production mode".
- Select a Cloud Firestore location for your database.
- Click "Create".

#### Add GCloud Key to GitHub Secrets:
Add the service account key to your Github Actions secrets  

1. Create a Service Account:
- Go to the Google Cloud Console.
- Select your project.
- Navigate to "IAM & Admin" > "Service accounts".
- Click "Create Service Account".
- Enter a name for the service account, select a role (e.g., "Cloud Datastore User" for Firestore), and click "Create".
- Click "Done" to finish creating the service account.
2. Download the Service Account Key:
- In the list of service accounts, find the one you just created.
- Click on the three dots under "Actions" and select "Manage keys".
- Click "Add Key" and choose "JSON".
- The key file will be downloaded to your computer. Keep this file secure and do not share it publicly.
3. Add the JSON Key to GitHub Secrets:
- Go to your GitHub repository.
- Click on "Settings" > "Secrets" > "New repository secret".
- Enter a name for the secret (`GOOGLE_CREDENTIALS`).
- Paste the JSON key into the "Value" field.
- Click "Add secret".

### Scrape Manual Trigger:
To trigger the scraper manually, go to the "Actions" tab in your repository, click on "Scrape" and then "Run workflow".
Just don't run two scrapers at the same time, it will cause a conflict.