import requests
import praw
import os
import time
import pickle
import datetime
from bs4 import BeautifulSoup

"""Planet Site Reddit Bot
Last update: May 21st, 2019

The purpose of this code is to scan inputted website news feeds, collect articles that are related to planets, and
posts them to the subreddit /r/PlanetExoplanet.
Meant to be run automatically throughout some time period."""


def save_obj(obj, name):
    """Saves a dictionary to be recalled later.

    Args:
        obj (dict): The dictionary to save
        name (str): What to name saved dictionary

    Returns:
        file (.pkl): File with already posted websites

    """
    with open(name + '.pkl', 'wb') as f:
        pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)


def load_obj(name):
    """Loads a dictionary. This is used to keep track of what has already been posted.

    Args:
        name (str): The name of the file to load

    Returns:
        f (dict): A dictionary object

    """
    with open(name + '.pkl', 'rb') as f:
        return pickle.load(f)


def post_to_reddit(reddit, title, link, posted):
    """Submits an individual post to the subreddit 'PlanetExoplanet'.

    Args:
        reddit: The file containing your credentials
        title (str): Title of the article
        link (str): Link of the article
        posted (dict): all articles already posted

    Returns:
        posted (dict): The updated list of posted articles

    """
    try:  # Check if article has already been posted
        print('%s is already posted.\n' % posted[title][0])

    except KeyError:  # If not, post the article to Reddit, then mark as posted
        try:
            reddit.subreddit('PlanetExoplanet').submit(title, url=link)
        except:
            reddit.subreddit('PlanetExoplanet').submit(title, selftext=link)
        posted[title] = [link, time.time()]
        time.sleep(5)  # Small pause so the account is not Banned for spam

    return posted  # Update posted articles dictionary


def standard_website(reddit, website, webpage, class_name, keywords, posted):
    """ Creates posts for a website that abides by news standards (one webpage feed, articles are under one class,
    titles are under <h2> tag, etc.).

    Args:
        reddit: The file containing your credentials
        website (str): Name of the website you are pulling stories from
        webpage (str): The url of the webpage that contains the news feed
        class_name (str): The HTML class used to mark stories
        keywords (list): Keywords to look for in article titles
        posted (dict): Articles that have been posted already

    Returns:
        posted (dict): Articles that have been posted already

    """
    # Pull webpage and parse through it
    page = requests.get(webpage)
    soup = BeautifulSoup(page.content, 'html.parser')

    # Find the titles/link through the HTML class they are under
    title_list = soup.find_all(class_=class_name)

    # Go through each class instance and separate titles/links.
    # If they have any keywords, try to submit them to Reddit.
    for number in range(len(title_list)):
        title = title_list[number].h2.text.strip()
        link = website + title_list[number].a['href']
        if any(keyword in title.lower() for keyword in keywords):
            posted = post_to_reddit(reddit, title, link, posted)

    return posted  # Update posted articles dictionary


def close_up(posted):
    """Takes the dictionary of posted articles, deletes old ones for space, and saves the file."""
    # Delete old articles to save space
    for i in list(posted):
        if time.time() - posted[i][1] > 12960000.0:
            del posted[i]
    # Save the articles that have already been posted
    save_obj(posted, 'planet_posted')


def main():
    keywords = ['planet', 'mercury', 'venus', 'mars', 'jupiter',
                'saturn', 'uranus', 'neptune', 'pluto', 'transit']

    # Login to Reddit and specify credentials
    reddit = praw.Reddit('bot1')

    # Load up the dictionary of articles already posted, or create new dictionary
    if not os.path.isfile("planet_posted.pkl"):
        posted = {}
    else:
        posted = load_obj("planet_posted")

    # -- Arxiv Section
    # Need it's own parser section due to unusual link type; posts on Saturdays only
    if datetime.datetime.today().weekday() == 5:
        page = requests.get("https://arxiv.org/list/astro-ph.EP/pastweek?skip=0&show=25")
        soup = BeautifulSoup(page.content, 'html.parser')
        title_list = soup.find_all(class_="list-title mathjax")
        link_list = soup.find_all(class_='list-identifier')
        title = 'arXiv postings for ' + str(datetime.datetime.today().strftime('%Y-%m-%d'))
        arxiv_post_list = ['%s\n%s\n\n' % (title_list[number].text.strip().replace("Title: ", ""),
                                           'https://arxiv.org' + link_list[number].a['href'])
                           for number in range(len(title_list))]
        arxiv_post = ''.join(arxiv_post_list)
        posted = post_to_reddit(reddit, title, arxiv_post, posted)

    # -- Astronomy Magazine Section
    posted = standard_website(reddit,
                              'http://www.astronomy.com',
                              "http://www.astronomy.com/news",
                              "content withImage", keywords, posted)
    # -- Space.com Section
    posted = standard_website(reddit,
                              'http://www.space.com',
                              "https://www.space.com/news?type=article|countdown|image_album\
                              |infographic|quiz|reference|wallpaper&section=science-astronomy",
                              "pure-u-3-4 pure-u-md-2-3 pure-u-lg-2-3 list-text",
                              keywords, posted)
    # -- Astrobites Section
    posted = standard_website(reddit,
                              "",
                              "https://astrobites.org/category/daily-paper-summaries/",
                              'post',
                              keywords, posted)

    close_up(posted)


if __name__ == '__main__':
    main()
