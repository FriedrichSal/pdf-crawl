import os
import sys
import io
import glob
import logging
from utils.request_utils import simple_get_html_or_pdf

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


PDF_FOLDER = "data/pdf_ankauf"


def fetch_and_save_pdf(url, filename=None):
    result = simple_get_html_or_pdf(url)
    status_code = "n/a"
    content_type = "n/a"
    if result is not None:
        (resp_content, status_code, content_type, resp_url) = result
        if (status_code == 200) and (content_type == "pdf"):
            if filename is not None:
                with open(os.path.join(PDF_FOLDER, filename), "wb") as f:
                    f.write(resp_content)
            return resp_content

    # Reach here only if something went wrong
    print(
        "Something went wrong - status {}, content type {}, url {}".format(
            status_code, content_type, url
        )
    )



