### Setup

To deploy this scraper you need to fork this repository.
I use `poetry` for dependency management, so you need to install it first.
After that, run `poetry shell` and `poetry install` to install all dependencies.


### Twitter Credentials:
You need to have a Twitter account and provide your credentials to the scraper.
To scrape Twitter you need session file, it can be created by running `twitter_sign_in.py`
Then navigate to your repository on GitHub, click on "Settings", then "Secrets", and finally "Actions". Click on "New repository secret" to add a new secret. Provide a name for your secret (`TWITTER_USERNAME` and `TWITTER_PASSWORD`) and the corresponding values, then click "Add secret".

### GitHub Actions:
You need to enable write access to the repository.
Go to your repository on GitHub, click on "Settings", then "Actions", "General" and at "Workflow permissions" enable "Read and write permissions".

![image](docs/gh_action.jpg)

### Scrape Manual Trigger:
To trigger the scraper manually, go to the "Actions" tab in your repository, click on "Scrape" and then "Run workflow".
Just don't run two scrapers at the same time, it will cause a conflict.