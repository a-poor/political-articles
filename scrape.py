
import re
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin


urls = [
    ("breitbart","https://www.breitbart.com/",r"breitbart")
]


class ArticleScraper:
    def __init__(self,dirname,start_url,url_pattern):
        # Settings 
        self.dirname = dirname
        self.start = start_url
        self.url_pattern = url_pattern
        # URL queues
        self.queue = set()
        self.active = set()
        self.checked = set()
        
    def validate_url(self,url):
        return bool(re.search(self.url_pattern,url))

    def get_page(self,url):
        resp = requests.get(url)
        return BeautifulSoup(resp.content,"lxml")

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
        self.active = self.queue()
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

    def scrape(self,depth=3):
        path = Path(self.dirname) 
        self.queue.add(self.start)
        for i in range(depth):
            self.link_step()
            for url in self.active:
                # Get the page
                soup = self.get_page(url)
                # Extract and save the text
                text = self.get_text(soup)
                filename = f"{hash(text)}"
                (path / filename).write_text(text)
                # Extract links
                links = self.get_links(soup)
                self.add_links(links)


if __name__ == "__main__":
    for site in urls:
        ArticleScraper(*site).scrape()

