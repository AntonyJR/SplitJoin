import asyncio
from datetime import datetime

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
    print("Headers")
    for header in reqheaders :
        print("  "+header+":"+reqheaders[header])
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
        print("id "+str(id)+" Deleted Content-Type")
        for header in headers:
            print("  "+header+":"+headers[header])

    url = query["url"]

    payload = query["payload"] if "payload" in query else None

    auth = None
    if "username" in query and "password" in query:
        auth = BasicAuth(login=query["username"],
                         password=query["password"])
        del headers["Authorization"]
        print("id "+str(id)+" Deleted Authorization")

    qheaders = query["headers"] if "headers" in query else {}
    for header in qheaders:
        if header in headers:
            del headers[header]
            print("id "+str(id)+" Deleted "+header)
        headers[header] = qheaders[header]

    try:
        async with session.request(method, url, json=payload, auth=auth, headers=headers, timeout=timeout) as response:
            if response.status < 200 or response.status > 299 or not response.content_type.endswith("json"):
                print("id "+str(id)+" Not json")
                result["message"] = await response.text()
                result["status"] = response.status
            else:
                result["response"] = await response.json()
                result["status"] = response.status
    except ClientResponseError as err:
        result["status"] = err.status
        result["message"] = err.message
    result["end"] = datetime.now().isoformat(sep=' ', timespec="auto")
    return result


app = web.Application()
app.add_routes([web.get('/', handle),
                web.get('/{name}', handle),
                web.post('/splitjoin', handler)])

if __name__ == '__main__':
    web.run_app(app)
