FROM python:3-slim

WORKDIR /usr/src/app

RUN pip install aiohttp
RUN pip install markdown
COPY splitjoin.py ./
COPY README.md ./

CMD [ "python", "./splitjoin.py" ]

ENV LOGGING WARNING

EXPOSE 8080