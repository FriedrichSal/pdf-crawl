FROM python:3.7

# poppler for pdftotext
# RUN apt-get update && apt-get -y install build-essential libpoppler-cpp-dev pkg-config python3-dev poppler-utils tesseract-ocr-[deu]

WORKDIR /app

COPY ./requirements.txt /app/requirements.txt

RUN pip install -r requirements.txt

ENV PYTHONPATH=/app

COPY . /app

ENV PYTHONUNBUFFERED=TRUE

EXPOSE 80



WORKDIR /app


CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 app:app
