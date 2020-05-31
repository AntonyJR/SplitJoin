import asyncio
from datetime import datetime
import logging
import os

from aiohttp import web, ClientSession, BasicAuth, ClientResponseError


async def handle(request):
    name = request.match_info.get('name', "Anonymous")
    text = "Hello, " + name
    return web.Response(text=text, content_type="text/html")


async def handler(request):
    req = await request.json()
    timeout = req["timeout"]
    tasks = []
    reqheaders = request.headers
    for header in reqheaders :
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
    headers = dict(headers)
    result = {}

    result["start"] = datetime.now().isoformat(sep=" ", timespec="auto")
    id = query["id"]
    result["id"] = id

    method = query["method"] if "method" in query else "POST"
    if method != "POST" and method != "PUT" and "Content-Type" in headers:
        del headers["Content-Type"]
        logging.info("Query ID %s Deleted Content-Type", str(id))
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
        logging.info("Query ID %s Deleted Authorization", str(id))

    qheaders = query["headers"] if "headers" in query else {}
    for header in qheaders:
        if header in headers:
            del headers[header]
            logging.info("Query ID %s Deleted %s", str(id), header)
        headers[header] = qheaders[header]

    try:
        async with session.request(method, url, json=payload, params=params, auth=auth, headers=headers, timeout=timeout) as response:
            if response.status < 200 or response.status > 299 or not response.content_type.endswith("json"):
                logging.info("Query Response ID %s Not json", str(id))
                result["message"] = await response.text()
            else:
                result["response"] = await response.json()
            result["headers"] = dict(response.headers)
            result["status"] = response.status
    except ClientResponseError as err:
        result["status"] = err.status
        result["message"] = err.message
        logging.error("Query Response ID %s Returned Status %d Message : %s", str(id), err.status, err.message)
    result["end"] = datetime.now().isoformat(sep=' ', timespec="auto")
    return result


app = web.Application()
app.add_routes([web.get('/', handle),
                web.get('/{name}', handle),
                web.post('/splitjoin', handler)])
def init_logging():
    loglevel = os.getenv("LOGGING", "WARNING").upper()
    numeric_log_level = getattr(logging, loglevel, logging.WARNING)
    logging.basicConfig(level=numeric_log_level)

if __name__ == '__main__':
    init_logging()
    web.run_app(app)
