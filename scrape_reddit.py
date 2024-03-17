import json
import os
import time
from functools import wraps
from typing import Callable, Dict, List, Optional

import requests
from bs4 import BeautifulSoup
from google.cloud import firestore


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


def scrape_posts(subreddit: str, num_clicks: int = 2) -> List[BeautifulSoup]:
    url = f"https://old.reddit.com/r/{subreddit}/new/"
    headers = {"User-Agent": "Mozilla/5.0"}
    posts = []

    @retry()
    def scrape(url):
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")
        new_posts = soup.find_all("div", class_="thing")
        url_next = soup.find("span", class_="next-button").a["href"]
        return new_posts, url_next

    for _ in range(num_clicks):
        new_posts, url_next = scrape(url)
        posts.extend(new_posts)
        url = url_next

    return posts


def clean_posts(posts: List[BeautifulSoup]) -> List[BeautifulSoup]:
    posts_clean = []
    for post in posts:
        tagline = post.find("p", class_="tagline").text
        if tagline.split()[0] == "promoted":
            continue
        else:
            posts_clean.append(post)
    return posts_clean


def extract_post_details(post_el: BeautifulSoup) -> Dict[str, str]:
    title = post_el.find("a", class_="title").text
    comments = post_el.find("a", class_="comments").text.split()[0]
    url = post_el.find("a", class_="comments")["href"]
    upvotes = post_el.find("div", class_="score unvoted").text
    post = {}
    post["title"] = title
    post["url"] = url
    try:
        post["nr_comments"] = int(comments)
    except ValueError:
        post["nr_comments"] = 0
    post["upvotes"] = upvotes
    return post


@retry()
def get_content(url: str) -> Dict[str, Optional[str]]:
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")
    content_div = soup.find("div", class_="expando")
    content_gallery = soup.find_all("a", class_="thumbnail")
    try:
        content_text = content_div.find("div", class_="md").text
    except AttributeError:
        content_text = None

    content = {}
    content["text"] = content_text
    content["gallery"] = [
        element["href"]
        for element in content_gallery
        if element["href"].startswith("http")
    ]
    return content


def scrape_reddit(
    subreddit: str, num_pages: int = 3, min_nr_comments: int = 10, max_posts: int = 30
) -> None:
    """
    Scrapes posts from a specified subreddit on Reddit, filters them based on
    the number of comments, retrieves the content for each post,
    and saves the filtered posts to a JSON file.

    Args:
        subreddit (str): The name of the subreddit to scrape.
        num_pages (int): The number of pages to scrape from the subreddit.
            Each page contains 25 posts.
            Defaults to 3, resulting in 75 posts (before filtering).
        min_nr_comments (int, optional): The minimum number of comments
            a post must have to be included. Defaults to 10.
        max_posts (int, optional): The maximum number of latests posts
            to include. Defaults to 30.

    Returns:
        None
    """
    print(f"Scraping r/{subreddit}...")
    posts = scrape_posts(subreddit, num_clicks=num_pages)

    print("Removing promoted posts")
    posts_clean = clean_posts(posts)

    print("Number of posts after cleaning:", len(posts_clean))
    posts_data = [extract_post_details(post) for post in posts_clean]

    # Filter posts based on minimum number of comments
    filtered_posts = []
    for post in posts_data:
        if post["nr_comments"] >= min_nr_comments:
            filtered_posts.append(post)
    print(
        f"Number of posts with at least {min_nr_comments} comments:",
        len(filtered_posts),
    )

    # Limit the number of posts if it exceeds the maximum limit
    if len(filtered_posts) > max_posts:
        print(f"Limiting number of posts to {max_posts}")
        filtered_posts = filtered_posts[:max_posts]

    print("Getting content for each post")
    counter = 0
    total_posts = len(filtered_posts)
    for post in filtered_posts:
        counter += 1
        if counter % 10 == 0:
            print(f"Progress: {counter}/{total_posts}")
        post["content"] = get_content(post["url"])

    # Save filtered posts to a JSON file
    folder_path = "data/reddit"
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    file_path = os.path.join(folder_path, f"raw_posts_{subreddit}.json")
    with open(file_path, "w") as f:
        json.dump(filtered_posts, f, indent=4)
    print(f"Posts saved to file: {file_path}")
    return file_path


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


if __name__ == "__main__":
    subreddit = os.environ.get("SUBREDDIT")
    num_pages = int(os.environ.get("NUM_PAGES"))
    min_nr_comments = int(os.environ.get("MIN_NR_COMMENTS"))
    print(num_pages)
    print(type(num_pages))
    data_path = scrape_reddit(subreddit, num_pages, min_nr_comments)
    add_document_to_firestore(data_path, collection=f"reddit_{subreddit}")
