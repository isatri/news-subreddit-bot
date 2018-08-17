import requests
from bs4 import BeautifulSoup
import praw
import os
import time
import pickle


def save_obj(obj, name):
    """Saves a dictionary as name.pkl"""
    with open(name + '.pkl', 'wb') as f:
        pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)


def load_obj(name):
    """loads a dictionary with name = name.pkl"""
    with open(name + '.pkl', 'rb') as f:
        return pickle.load(f)


def post_to_reddit(reddit, title, link, posted):

    # Try to print the link to an article
    try:
        print('%s is already posted.\n' % posted[title])
    # If it fails, post the article to Reddit and mark as posted
    except KeyError:
        reddit.subreddit('PlanetExoplanet').submit(title, url=link)
        posted[title] = link
        time.sleep(5)  # Wait a bit so you don't get banned from Reddit if high number of posts

    return posted  # Update posted articles dictionary


def standard_website(reddit, website, webpage, class_name, keywords, posted):
    """Function for a standard website that has one webpage feed, where the article title
    and link is under one class (title must be under <h2> tag)"""

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


def main():
    keywords = ['planet', 'mercury', 'venus', 'mars', 'jupiter', 'saturn', 'uranus', 'neptune', 'pluto', 'transit']

    reddit = praw.Reddit('bot1')  # Login to Reddit and specify credentials

    # Load up the dictionary of articles already posted, or create new dictionary
    if not os.path.isfile("planet_posted.pkl"):
        posted = {}
    else:
        posted = load_obj("planet_posted")

    # -- Arxiv Section
    page = requests.get("https://arxiv.org/list/astro-ph.EP/pastweek?skip=0&show=25")
    soup = BeautifulSoup(page.content, 'html.parser')
    title_list = soup.find_all(class_="list-title mathjax")
    link_list = soup.find_all(class_='list-identifier')
    for number in range(len(title_list)):
        title = title_list[number].text.strip().replace("Title: ", "")
        link = 'https://arxiv.org' + link_list[number].a['href']
        if any(keyword in title.lower() for keyword in keywords):
            posted = post_to_reddit(reddit, title, link, posted)

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

    # Save the articles that have already been posted
    save_obj(posted, 'planet_posted')


if __name__ == '__main__':
    main()
