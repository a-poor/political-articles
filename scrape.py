
import re
import time
import random
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

import logging


logger = logging.getLogger(__name__)
logging.basicConfig(
    filename="article-scrape.log",
    format="[%(asctime)s] %(levelname)s:  %(message)s",
    level=logging.INFO
)


urls = [
    ("breitbart","https://www.breitbart.com/",r"breitbart"),
    ("fox","https://www.foxnews.com/","fox"),
    ("infowars","https://www.infowars.com/","infowars"),
    ("drudgereport","https://www.drudgereport.com/","drudgereport"),
    ("nypost","https://nypost.com/","nypost"),
    ("dailywire","https://www.dailywire.com/","dailywire"),
    ("gatewaypundit","https://www.thegatewaypundit.com/","gatewaypundit"),

    ("jacobin","https://jacobinmag.com","jacobin"),
    ("jezebel","https://jezebel.com/","jezebel"),
    ("vice","https://www.vice.com/en_us/section/news","vice"),
    ("vox","https://www.vox.com/","vox"),
    ("dailybeast","https://www.thedailybeast.com/","thedailybeast"),
    ("motherjones","https://www.motherjones.com/","motherjones"),
    ("salon","https://www.salon.com/","salon"),

    ("cnn","https://www.cnn.com/","cnn"),
    ("abc","https://abcnews.go.com/","abcnews"),
    ("nbc","https://www.nbcnews.com/","nbcnews"),
    
    ("politico","https://www.politico.com/","politico"),
    ("npr","https://www.npr.org/","npr"),
    
    ("apnews","https://apnews.com/","apnews"),
    ("reuiters","https://www.reuters.com/news/us","reuiters"),

]

class ArticleScraper:
    def __init__(self,dirname,start_url,url_pattern=None,max_retries=5):
        # Settings 
        self.dirname = dirname
        self.start = start_url
        if url_pattern is None:
            url_pattern = ".*"
        else:
            self.url_pattern = url_pattern
        self.max_retries = max_retries
        # URL queues
        self.queue = set()
        self.active = set()
        self.checked = set()
        
    def validate_url(self,url):
        return (re.match("mailto",url) is not None and
                re.search(self.url_pattern,url) is not None)

    def get_page(self,url):
        for ri in range(self.max_retries+1):
            try:
                resp = requests.get(url)
            except Exception as e:
                retrying = ri < self.max_retries + 1

                sleep_time = max(10 ** ri + random.gauss(5,2),0.1)

                logger.error(f"{self.dirname} | Request error: {e} | Retrying: {retrying}")
                if retrying:
                    logger.info("{self.dirname} | Sleeping for {sleep_time}s")
                    time.sleep(sleep_time)
            else:
                return BeautifulSoup(resp.content,"lxml")
        return None

    def get_links(self,soup):
        a_tags = soup.find_all("a")
        urls = [a.attrs.get("href") for a in a_tags]
        return [self.abs_url(url) for url in urls]

    def get_text(self,soup):
        p_tags = soup.find_all("p")
        text = " ".join(p.text for p in p_tags)
        return re.sub(r"\s+"," ",text.strip())

    def link_step(self):
        self.checked = self.checked.union(self.active)
        self.active = self.queue
        self.queue = set()

    def add_link(self,url):
        if (url not in self.checked and
            url not in self.active and
            self.validate_url(url)):
            self.queue.add(url)

    def add_links(self,urls):
        [self.add_link(url) for url in urls]

    def abs_url(self,url):
        return urljoin(self.start,url)

    def scrape(self,depth=3,data_dir="."):
        fn = time.strftime("%Y%m%d-%H%M%S") + f"_{self.dirname}_"
        data_dir = Path(data_dir)
        if not data_dir.exists():
            data_dir.mkdir()
        path = data_dir / Path(self.dirname)
        if not path.exists():
            path.mkdir()
        logger.info(f"{self.dirname} | Saving data to {path}")
        self.queue.add(self.start)
        for i in range(depth):
            self.link_step()
            logger.info(f"{self.dirname} | Scrape depth {i}. Scraping {len(self.active)} pages")
            for url in self.active:
                # Get the page
                soup = self.get_page(url)
                if soup is None:
                    logger.info(f"{self.dirname} | Couldn't read page. Skipping.")
                    continue
                # Extract and save the text
                text = self.get_text(soup)
                filename = path / f"{fn}{hash(text)}.txt"
                filename.write_text(text)
                # Extract links
                links = self.get_links(soup)
                logger.info(f"{self.dirname} | Found {len(links)} links")
                self.add_links(links)
        logger.info(f"{self.dirname} | Scraped a total of {len(self.checked)} links.")


if __name__ == "__main__":
    logger.info("Starting")
    random.shuffle(urls)
    for site in urls:
        logger.info(f"Scraping site: {site[0]}")
        ArticleScraper(
            *site,
            max_retries=5
        ).scrape(
            depth=3,
            data_dir="./data"
        )
    logger.info("Done.")


