"""
Implements tasks callable from redis worker
"""
import logging
import io
import datetime
import pytz
import requests
import json

from file_crawl import filecrawl_test, get_pdf_urls_from_site
from utils.pdf_wrangler import fetch_and_save_pdf
from utils.request_utils import simple_get_html_or_pdf

logger = logging.getLogger(__name__)



def filecrawl_with_url(website_url, num_layers=2):
    """Task for crawling website and storing result in crawldb.
    Crawls website_url and stores (inserts or updates) resulting pdf_urls and html_urls in database. 
    Also inserts/updates the entry for website_url. 

    Keyword arguments: 
        website_url: string, url to crawl
    
    Returns None

    """
    # Add http protocol if necessary
    if website_url.startswith("http"):
        url = website_url
    else:
        url = "http://" + website_url

    # Crawl site and fetch all urls
    out = get_pdf_urls_from_site(url, num_layers=num_layers)
    if out is None:
        logger.info("{} is DEAD.".format(website_url))
        return {"status": "DEAD"}

    logger.info("{} processed. DONE".format(website_url))
    out["STATUS"] = "OK"
    return out

