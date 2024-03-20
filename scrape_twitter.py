import datetime
import json
import os
import time
from functools import wraps
from typing import Callable, List

from google.cloud import firestore
from tweety import Twitter
from tweety.types.twDataTypes import SelfThread


def retry(max_retries: int = 3, delay: int = 60, backoff: int = 15) -> Callable:
    """
    Decorator that retries a function a specified number of times with a delay
    between retries.

    Args:
        max_retries (int): The maximum number of retries. Default is 3.
        delay (int): The delay in seconds between retries. Default is 60.
        backoff (int): The factor by which the delay increases after each retry.
        Default is 15.

    Returns:
        Callable: The decorated function.

    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            mtries, mdelay = max_retries, delay
            while mtries > 1:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    msg = f"{func.__name__} failed with {str(e)},"
                    msg += f" Retrying in {mdelay} seconds..."
                    print(msg)
                    time.sleep(mdelay)
                    mtries -= 1
                    mdelay *= backoff
            return func(*args, **kwargs)

        return wrapper

    return decorator


def save_tweets(tweet_data: List[dict], keyword: str) -> None:
    class DateTimeEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, datetime.datetime):
                return obj.isoformat()
            return super().default(obj)

    folder_path = "data/twitter"
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    file_path = os.path.join(folder_path, f"raw_tweets_{keyword}.json")
    with open(file_path, "w") as file:
        file.write(json.dumps(tweet_data, cls=DateTimeEncoder))
    print(f"Tweets saved: {file_path}")
    return file_path


def extract_tweet_data(tweet: dict) -> dict:
    tweet_dict = {}
    if isinstance(tweet, SelfThread):
        tweet = tweet.tweets[-1]
    for key in tweet.keys():
        tweet_dict[key] = tweet[key]
    return tweet_dict


def save_tweets_to_file(tweets: List[dict], keyword: str, nr_tweets: int = 15) -> None:
    tweet_data = []
    for tweet in tweets[:nr_tweets]:
        tweet_data.append(extract_tweet_data(tweet))
    return save_tweets(tweet_data, keyword)


def save_top_tweets_to_file(
    tweets: List[dict], keyword: str, nr_top_tweets: int = 3
) -> None:
    tweet_data = []
    for tweet in tweets:
        tweet_data.append(extract_tweet_data(tweet))
    for tweet in tweet_data:
        tweet["likes"] = int(tweet["likes"])
    sorted_tweets = sorted(tweet_data, key=lambda x: x["likes"], reverse=True)
    top_tweets = sorted_tweets[:nr_top_tweets]
    return save_tweets(top_tweets, keyword)


@retry()
def get_user_tweets(app, handle, pages):
    return app.get_tweets(handle, pages)


@retry()
def get_hashtag_tweets(app, hashtag, min_faves, pages):
    return app.search(f"min_faves:{min_faves} #{hashtag}", pages)


def simplify_tweets(tweet_data):
    simple_tweets = []
    for tweet in tweet_data:
        simple_tweet = {}
        simple_tweet["username"] = tweet["author"]["username"]
        for k in ("id", "created_on", "text", "likes", "url"):
            simple_tweet[k] = tweet[k]
        simple_tweets.append(simple_tweet)
    return simple_tweets


def simplify_and_save_tweets(tweet_file: str) -> None:
    with open(tweet_file, "r") as file:
        tweet_data = json.load(file)
    simple_tweets = simplify_tweets(tweet_data)
    simple_tweet_file = tweet_file.replace("raw", "simple")
    with open(simple_tweet_file, "w") as file:
        json.dump(simple_tweets, file, indent=4)
    return simple_tweet_file


@retry()
def add_document_to_firestore(data_path, collection: str):
    with open(data_path, "r") as file:
        data = json.load(file)
    # Initialize Firestore client
    db = firestore.Client()
    # Create a reference to the document
    doc_ref = db.collection(collection).document()
    # Define the data to be stored in the document
    # Set the document data
    if isinstance(data, list):
        data = {"data": data}  # Wrap the list in a dictionary
    doc_ref.set(data)
    print(f"Document successfully written to {collection}")


def main(app: Twitter, handle: str, hashtag: str, min_faves: int, h_pages: int) -> None:
    """
    Main function for scraping Twitter data.

    Args:
        app (Twitter): The Twitter application object.
        handle (str): The Twitter user handle to scrape tweets from.
        hashtag (str): The hashtag to search for tweets.
        min_faves (int): The minimum number of likes a tweet must have to be considered.
        h_pages (int): The number of pages to scrape for hashtag tweets.
            More pages will result in more tweets, but it can be Rate Limited.

    Returns:
        None
    """
    all_tweets = get_user_tweets(app, handle, pages=2)
    user_tweets = save_tweets_to_file(all_tweets, keyword=handle, nr_tweets=15)
    add_document_to_firestore(user_tweets, collection=f"twitter_user_{handle}")

    search_top = get_hashtag_tweets(app, hashtag, min_faves, pages=h_pages)
    hashtag_tweets = save_top_tweets_to_file(search_top, keyword=hashtag)
    add_document_to_firestore(hashtag_tweets, collection=f"twitter_trends_{hashtag}")

    simpl_user = simplify_and_save_tweets(user_tweets)
    add_document_to_firestore(simpl_user, collection=f"twitter_user_{handle}_simple")
    simpl_hashtag = simplify_and_save_tweets(hashtag_tweets)
    add_document_to_firestore(
        simpl_hashtag, collection=f"twitter_trends_{hashtag}_simple"
    )


if __name__ == "__main__":

    app = Twitter("session")
    username = os.getenv("TWITTER_USERNAME")
    password = os.getenv("TWITTER_PASSWORD")
    app.sign_in(username, password)
    handle = os.environ.get("HANDLE")
    hashtag = os.environ.get("HASHTAG")
    min_faves = int(os.environ.get("MIN_FAVES"))
    h_pages = int(os.environ.get("PAGES"))

    main(app, handle, hashtag, min_faves, h_pages)
