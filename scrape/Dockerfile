FROM python:3.8
WORKDIR /app
COPY scrape.py /app
COPY scrape-requirements.txt /app
RUN pip install -r /app/scrape-requirements.txt
CMD [ "python", "scrape.py" ]
