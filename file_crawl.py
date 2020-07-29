"""
Implements function to crawl root domain to a certain depth degree
Link pointing outside the root domain are avoided. 
"""
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

import os
import time
import requests
from requests.exceptions import RequestException, ConnectionError
from contextlib import closing
from bs4 import BeautifulSoup
import re
import io
import json
import six
from urllib.parse import urljoin
import argparse
from urllib.parse import urlparse
from urllib.parse import quote
import datetime

from utils.request_utils import validate_url, domain_from_url, simple_get_html_or_pdf

def filecrawl_test(website_url):
    # Test task
    logger.info('Crawling site {}'.format(website_url))
    return None


def get_pdf_urls_from_site(website_url, num_layers=2):
    """Crawl site of given website url for PDF ULRs and return them.
    Keyword arguments:
        webiste_url: string, url of the site to crawl
        num_layers: integer, degree to which depth to crawl the side (max distance of any link to website_url)
    
    Returns: a dictionary with keys
        pdf_urls: list of strings of links yielidng pdf responses
        html_urls: list of strings of all links yielding html repsonses
        resp_url: url that came back as response when querying webiste_url
        num_html: lenght of html_urls
    """

    # Check if this is redirect
    try:
        (resp_content, status_code, content_type, resp_url) = simple_get_html_or_pdf(website_url)
    except TypeError:
        logger.error('Root url {} is not reachable. Abort.'.format(website_url))
        return None
    if resp_url != website_url:
        logger.info("Root url {} changed to resp_url {} (due to alias/redirect) for correct domain filtering".format(website_url, resp_url))
        website_url = resp_url

    pdf_urls = set()
    # Return if website url on blacklisted site
    black_list = [
        "berlin-airport.de",
        "fonts.googleapis.com",
        "wordpress.com",
        "conzuela",
        "stadtteilzeitung",
    ]
    if any([domain in website_url for domain in black_list]):
        logger.warning("Website URL {} is blacklisted".format(website_url))
        return set()

    # Get all unique urls from home page which are pointing to pages on that site
    site_urls_first_layer = scrape_site_urls_from_page(website_url)
    site_urls_first_layer = list(set(site_urls_first_layer))

    logger.info("Found {} pages linked directly on {}".format(len(site_urls_first_layer), website_url))



    # second layer
    # site_urls = site_urls_first_layer
    site_urls_second_layer = None
    if num_layers > 1:
        for url in site_urls_first_layer:
            site_urls = scrape_site_urls_from_page(url)
            if site_urls is not None:
                site_urls_second_layer = site_urls + ( site_urls_second_layer or [])
                logger.info("Found {} pages linked 2nd level on {}".format(len(site_urls), url))
        if site_urls_second_layer is not None:
            site_urls_second_layer = list(set(site_urls_second_layer))

    site_urls = site_urls_first_layer + (site_urls_second_layer or []) 

    
    # third layer
    if num_layers > 2:
        site_urls_third_layer = None
        for url in site_urls_second_layer:
            site_urls = scrape_site_urls_from_page(url)
            if site_urls is not None:
                site_urls_third_layer = site_urls + ( site_urls_third_layer or [])
                logger.info("Found {} pages linked 3rd level on {}".format(len(site_urls), url))
        site_urls_third_layer = list(set(site_urls_third_layer))

        # 
        # site_urls = site_urls_first_layer + (site_urls_second_layer or [])+ (site_urls_third_layer or [])
        site_urls = site_urls + (site_urls_third_layer or [])


    # add site url back in and remove duplicates
    if website_url not in site_urls:
        site_urls = [website_url] + site_urls
    site_urls = list(set(site_urls))
    logger.info("Found total {} pages after removing duplicates".format(len(site_urls)))

    # Make sure site_urls includes at least home page!
    if site_urls is None:
        site_urls = [website_url]

    # For every page in site_urls, get all pdf urls
    for page_url in site_urls:
        pdf_urls_on_page = scrape_pdf_urls_from_page(page_url)
        # Only add new ones to set of pdf urls
        n_pdf_before = len(pdf_urls)
        pdf_urls = pdf_urls.union(pdf_urls_on_page)
        logger.info("Found {} ({} new) PDF links on  {}".format(len(pdf_urls_on_page), len(pdf_urls) - n_pdf_before, page_url))
        # if '.pdf' in page_url:
        #     import ipdb; ipdb.set_trace()

    # Remove all URLs pointing to blacklisted sites
    pdf_urls = [
        pdf_url
        for pdf_url in pdf_urls
        if not any([domain in pdf_url for domain in black_list])
    ]


    return {
        'pdf_urls': pdf_urls,
        'html_urls': site_urls,
        'resp_url': resp_url,
        'num_html': len(site_urls),
        'num_pdf': len(pdf_urls),
        'num_layers': num_layers,
        'base_url': website_url,
        'crawl_time': str(datetime.datetime.now())

    }


def scrape_site_urls_from_page(page_url):
    """ Scrapes site urls from page
    :param base_url: absolute url to web page
    :return: urls is a list of strings containing unique urls to pages on that site which are referenced on the home page, plus the home page itself!

    """

    # base_url = page_url

    # Clean the url of named anchors (/#etc.)
    if page_url.find("#") != -1:
        page_url = page_url[: page_url.find("#")]

    try:
        (resp_content, status_code, content_type, resp_url) = simple_get_html_or_pdf(page_url)
    except TypeError:
        return None
    if content_type == 'pdf':
        return None

    soup = BeautifulSoup(resp_content, "html.parser")

    # Probably we should rather limit our search for URLs to anchor tags ('a'), href attributes are used very often without linking to web pages
    anchors = soup.find_all("a", href=True)
    urls = [tag.get("href") for tag in anchors]

    # Clean each url found on page of named anchors (/#etc.)
    urls = [re.sub("#.*$", "", url) for url in urls]

    # Clean of trailing newlines and space
    urls = [url.strip() for url in urls]

    # Remove duplicates (after(!) cleaning urls)
    urls = list(set(urls))

    # Remove urls to images, pdfs, etc.
    urls = [
        url
        for url in urls
        if not url.endswith(".css")
        and not url.endswith(".js")
        and not url.endswith(".png")
        and not url.endswith("jpg")
        and not url.endswith("gif")
        and not url.endswith("pdf")
        and not url.endswith("mov")
        and not url.endswith("mp3")
        and not url.endswith("mp4")
        and not url.endswith("mpeg")
        and not url.endswith("swf")
        and not url.endswith("svg")
        and not "mailto" in url
        and not "css" in url
        and not "json" in url
        and not "xml" in url
    ]

    # Find base url - look for base tag
    base_tag = soup.find("base", href=True)
    if base_tag:
        base_url = base_tag.get("href")
    else:
        base_url = page_url


    # Transform relative urls into absolute urls
    absolute_urls = []
    # domain_url = domain_from_url(base_url)
    for url in urls:
        if url.startswith("http"):
            absolute_url = url
        else:
            absolute_url = urljoin(base_url, url)  # or domain_url ?

        absolute_urls.append(absolute_url)  # use set and .union?
        # remove validation - re not perfect - what can go wrong?
        # some urls where erroneoursly discarded
        # if absolute_url and validate_url(absolute_url):
        #     absolute_urls.append(absolute_url)  # use set and .union?
        # else:
        #     logger.warning('Invalid absolute url {}'.format(absolute_url))

    # Again remove duplicates which might have been included by transforming relative urls
    absolute_urls = list(set(absolute_urls))

    # Get rid of any URLs from outside domain
    domain = domain_from_url(page_url, addscheme=False)

    n = len(absolute_urls)
    urls = [url for url in absolute_urls if domain_from_url(url, addscheme=False) == domain]
    if len(urls) < n:
        logger.info("Removed {} urls that pointed to other domains".format(n - len(urls)))
        removed_urls = [url for url in absolute_urls if domain_from_url(url, addscheme=False) != domain]
        for url in removed_urls:
            logger.info('Removed link to domain {}'.format(domain_from_url(url)))

    return urls


def scrape_pdf_urls_from_page(page_url):
    """
    Scrapes pdf urls for pdf files from page

    :param page_url: string, absolute url to web page
    :return: set of strings containing urls to pdf files
    """

    # logger.info('Scrape pdf urls from page with URL: {}'.format(page_url))

    pdf_urls = set()  # avoid duplicates by using set instead of list

    try:
        (resp_content, status_code, content_type, resp_url) = simple_get_html_or_pdf(page_url)
    except TypeError:
        return set()
    if content_type == 'pdf':
        return {page_url}

    soup = BeautifulSoup(resp_content, "html.parser")

    # The following code scrapes any PDF URL inside any href-Attribute (or part of it) of any tag
    # This might take considerably longer than just taking into account the anchor tags
    tags = soup.find_all(href=True)
    for tag in tags:
        url = tag.get("href")
        if url.endswith(".pdf"):
            if url.startswith("http"):
                absolute_url = url
                # logger.info('Found absolute pdf URL: {}'.format(absolute_url))
            else:
                # Transform relative URL to absolute
                absolute_url = urljoin(page_url, url)
                # logger.info('Created absolute pdf URL: {}'.format(absolute_url))

            pdf_urls.add(absolute_url)

    return pdf_urls




if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--url', type=str, default='http://www.dewag.de',
                        help='input url to craws')
    args, unparsed = parser.parse_known_args()
    logger.info("Called file_crawl with {}".format(args.url))
    result = get_pdf_urls_from_site(args.url)
    if result is not None:
        pdf_urls = result['pdf_urls']
        resp_url = result['resp_url']
        num_html = result['num_html']
        if pdf_urls is not None:
            logger.info('Found {} PDF links for {}'.format(len(pdf_urls), args.url))
            print("======== Found these PDFS:")
            [print(url) for url in pdf_urls]
            print("======== containing Ankauf:")
            keywords = ['ankauf', 'anlagekriterien','anforderungsprofil']
            # [print(url) for url in pdf_urls if ('ankauf' in url.lower()) or ('anlagekriterien' in url.lower())]
            [print(url) for url in pdf_urls if any(keyword in url.lower() for keyword in keywords)]
        else:
            logger.info("No PDFs found.")
    else:
        logger.info("No PDFs found.")
    