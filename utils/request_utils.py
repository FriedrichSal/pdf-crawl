import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
import re
import requests
from urllib.parse import urlparse
from contextlib import closing
from requests.exceptions import RequestException, ConnectionError


def validate_url(url):
    regex = re.compile(
            r'^(?:http|ftp)s?://' # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' #domain...
            r'localhost|' #localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
            r'(?::\d+)?' # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    check = re.match(regex, url) is not None
    if not check:
        import ipdb; ipdb.set_trace()

    return check 


def domain_from_url(url, addscheme=True):
    # Get domain from url, for example - returns http://www.google.com for http://www.google.com/bla/bla
    # From https://stackoverflow.com/questions/9626535/get-protocol-host-name-from-url
    try:
        parsed_uri = urlparse(url)
    except:
        logger.warning("Could not get domain from url {} - badly formed?".format(url))
        return None
    if addscheme:
        result = '{uri.scheme}://{uri.netloc}'.format(uri=parsed_uri)
    else:
        result = '{uri.netloc}'.format(uri=parsed_uri)

    return result



"""Helper functions from https://realpython.com/python-web-scraping-practical-introduction/"""
def simple_get_html_or_pdf(url):
    """
    Attempts to get the content at `url` by making an HTTP GET request.
    If the content-type of response is some kind of HTML/XML, return the
    text content, otherwise return None
    """
    try:
        with closing(requests.get(url, stream=True, timeout=7)) as resp:
            content_type = resp.headers["Content-Type"].lower()
            if content_type.find('html') > -1:
                content_type = 'html'
            elif content_type.find('pdf') > -1:
                content_type = 'pdf'
            else:
                logger.warning("Wrong content type {}. Returning None".format(content_type))
                return None
            return resp.content, resp.status_code, content_type, resp.url

    except (RequestException, UnicodeDecodeError, KeyError) as e:
        logger.error("Error during requests to {0} : {1}".format(url, str(e)))
        return None
