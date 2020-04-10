FROM python:3-slim

WORKDIR /usr/src/app

RUN pip install aiohttp
COPY splitjoin.py ./

CMD [ "python", "./splitjoin.py" ]

EXPOSE 8080