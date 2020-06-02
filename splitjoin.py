import asyncio
import logging
import os
from datetime import datetime

import markdown
import redis
from aiohttp import web, ClientSession, BasicAuth, ClientResponseError

CACHE_SOCKET_TIMEOUT = 0.5
CACHE_CONNECTION_TIMEOUT = 2.0

global helpscreen
global cache
cache = None


# noinspection PyUnusedLocal
async def handlehelp(request):
    return web.Response(text=helpscreen, content_type="text/html")


async def handler(request):
    req = await request.json()
    timeout = req["timeout"]
    tasks = []
    reqheaders = request.headers
    for header in reqheaders:
        logging.info("Inbound Request Header %s : %s", header, reqheaders[header])
    headers = dict(reqheaders)
    del headers["Host"]
    del headers["Content-Length"]
    del headers["Connection"]
    async with ClientSession() as session:
        for query in req["queries"]:
            task = asyncio.create_task(caller(session, query, timeout, headers))
            tasks.append(task)
        queries = await asyncio.gather(*tasks)
    return web.json_response(queries)


async def caller(session, query, timeout, headers):
    global cache
    headers = dict(headers)
    result = {"start": datetime.now().isoformat(sep=" ", timespec="auto")}

    qid = query["id"]
    result["id"] = qid
    method = query["method"] if "method" in query else "POST"
    cachekey = query["cachekey"] if "cachekey" in query else None
    cachedresult = None

    if cache is not None and cachekey is not None:
        try:
            cachevalue = cache.get(cachekey)
            if cachevalue is not None:
                cachedresult = eval(cachevalue)
                cachedresult["start"] = result["start"]
                result = cachedresult
                logging.info("Retrieved cache record key %s", cachekey)
        except ValueError:
            logging.error('Value type not found in cache record key %s', cachekey)
            cachedresult = None
        except (redis.exceptions.TimeoutError, redis.exceptions.ConnectionError):
            logging.error('Error retrieving from cache')
            cachedresult = None

    if cachedresult is None:
        if method != "POST" and method != "PUT" and "Content-Type" in headers:
            del headers["Content-Type"]
            logging.info("Query ID %s Deleted Content-Type", str(qid))
            for header in headers:
                logging.info("Copy Header to Query %s : %s", header, headers[header])

        url = query["url"]

        payload = query["payload"] if "payload" in query else None

        params = query["params"] if "params" in query else None

        auth = None
        if "username" in query and "password" in query:
            auth = BasicAuth(login=query["username"],
                             password=query["password"])
            del headers["Authorization"]
            logging.info("Query ID %s Deleted Authorization", str(qid))

        qheaders = query["headers"] if "headers" in query else {}
        for header in qheaders:
            if header in headers:
                del headers[header]
                logging.info("Query ID %s Deleted %s", str(qid), header)
            headers[header] = qheaders[header]

        try:
            async with session.request(method, url, json=payload, params=params, auth=auth, headers=headers,
                                       timeout=timeout) as response:
                if response.status < 200 or response.status > 299 or not response.content_type.endswith("json"):
                    logging.info("Query Response ID %s Not json", str(qid))
                    result["message"] = await response.text()
                else:
                    result["response"] = await response.json()
                result["headers"] = dict(response.headers)
                result["status"] = response.status
                if cache is not None and cachekey is not None:
                    try:
                        result["cached"] = datetime.now().isoformat(sep=' ', timespec="auto")
                        ttl = query["cachettl"] if "cachettl" in query else None
                        cache.set(cachekey, str(result), ex=ttl)
                        logging.info("Cached result for key %s", cachekey)
                    except (redis.exceptions.TimeoutError, redis.exceptions.ConnectionError, redis.exceptions.DataError):
                        logging.error('Error storing to cache for key %s', cachekey)
        except ClientResponseError as err:
            result["status"] = err.status
            result["message"] = err.message
            logging.error("Query Response ID %s Returned Status %d Message : %s", str(qid), err.status, err.message)

    result["end"] = datetime.now().isoformat(sep=' ', timespec="auto")
    return result


def init_app():
    app = web.Application()
    app.add_routes([web.get('/{tail:.*}', handlehelp),
                    web.post('/{tail:.*}', handler)])
    web.run_app(app)


def init_cache():
    global cache
    cachehostname = os.getenv('REDIS_HOST')
    cacheport = int(os.getenv('REDIS_PORT', '6379'))
    cachepassword = os.getenv('REDIS_PASSWORD')
    if cachehostname is not None:
        try:
            cache = redis.Redis(host=cachehostname, port=cacheport, password=cachepassword,
                                socket_connect_timeout=CACHE_CONNECTION_TIMEOUT, socket_timeout=CACHE_SOCKET_TIMEOUT)
            logging.info(cache.info())
        except redis.exceptions.TimeoutError:
            logging.error('Unable to connect to Cache %s:%d - Running without cache', cachehostname, cacheport)
        except redis.exceptions.AuthenticationError:
            logging.error('Invalid authentication for cache %s:%d - Running without cache', cachehostname, cacheport)


def init_helpscreen():
    with open('README.md', 'r') as readmeFile:
        global helpscreen
        helpscreen = markdown.markdown(readmeFile.read())
    logging.info('Help Screen Initialized')


def init_logging():
    loglevel = os.getenv("LOGGING", "WARNING").upper()
    numeric_log_level = getattr(logging, loglevel, logging.WARNING)
    logging.basicConfig(level=numeric_log_level)
    logging.info('Logging Initialized')


if __name__ == '__main__':
    init_logging()
    init_helpscreen()
    init_cache()
    init_app()
