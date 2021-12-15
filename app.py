"""
Webapi for finding all pdf files on a website

"""

import argparse
import logging
import json
from flask import Flask, request
from flask_restful import Resource, Api

from tasks import (
    filecrawl_with_url,
)

logger = logging.getLogger(__name__)

app = Flask(__name__)
api = Api(app)


# Test Resource
class HelloWorld(Resource):
    def get(self):
        return {"hello": "world"}


# Resource for crawling websites
class CrawlTask(Resource):
    def get(self):
        return {"use a ": "post request"}

    def post(self):
        # Crawl domain as given in payload field website_url.
        # Result is stored in the database
        url = request.form["url"]
        layers = request.form.get("layers") or 2
        layers = int(layers)
        out = filecrawl_with_url(website_url=url, num_layers=layers)
        print(out)
        if out is None:
            out = {"query_url": {url}, "status": "error"}
        else:
            out["query_url"] = url
        return out


# Define Routes for resources
api.add_resource(CrawlTask, "/crawl")
api.add_resource(HelloWorld, "/")


if __name__ == "__main__":
    # Parse arguments on how to start the web app
    parser = argparse.ArgumentParser(description="parse arguments.")
    parser.add_argument(
        "-p",
        "--port",
        type=int,
        nargs=1,
        default=[80],
        help="port on which to serve the app",
        metavar="PORT",
    )
    parser.add_argument(
        "--dev", action="store_true", help="serve with flask dev server"
    )
    args = parser.parse_args()
    port = args.port[0]
    use_dev_server = args.dev

    # Dev or production server
    # host 0.0.0.0 to allow for outside connections
    logger.info("start dash with flask development server")
    app.run(port=port, debug=True, host="0.0.0.0")

