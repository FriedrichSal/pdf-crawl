# PDF Crawl

Web service for retrieving list of urls form web domain. The urls are classified into PDF and other. 

## How to use
Install dependencies with `pipenv install`, then start the service with

```bash
pipenv run python app.py -p 8080
```

Then you can query from localhost like so

```bash
curl localhost:8080/crawl -d "url=https://www.centralpark-hamburg.de" -X POST
```

By default, the search is two layers deep. You can go one level deeper by querying

```bash
curl localhost:8080/crawl -d "url=https://www.centralpark-hamburg.de&layers=3" -X POST
```
