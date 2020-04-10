import asyncio
from datetime import datetime

from aiohttp import web, ClientSession, BasicAuth, ClientResponseError


async def handle(request):
    name = request.match_info.get('name', "Anonymous")
    text = "Hello, " + name
    text += """
<H1>Splitjoin Microservice</H1>
<P>
This service takes a list of payloads and endpoints and sends the requests to all the endpoints in parallel.
It then collects the results and returns the results as a list of responses.
To call splitjoin <B>POST</B> to URL <B>/splitjoin</B>
</P>
<H2>Authentication</H2>
<P>Authentication has the following options:</P>
<DL>
    <DT>No Authentication</DT>
    <DD>If no Authorization header is passed to the service and username/password are not specified in the query then
    the call is made without authentication</DD> 
    <DT>Query Specific Basic Authentication</DT>
    <DD>If username and password are specified in the query then
    the call is made using basic authentication</DD> 
    <DT>Pass Through Authentication</DT>
    <DD>If no username/password are specified in the query and the request has an Authorization header
    then call is made using passed in authorization header.
    This allow the authentication to be passed through to the target API unchanged.</DD> 
</DL>

<H2>Base Request Structure</H2>
<P>
Base request to service has following structure:
<pre>
{
	"timeout" : 30,
	"queries" : [
		{
			"id" : "id1",
			"url" : "https://server/path",
			"username" : "OptionalUsername",
			"password" : "OptionalPassword",
			"payload" : {
				"any" : "payload",
				"goes" : "here""
			}
		},
		{
			"id" : "id2",
			"url" : "https://server/path",
			"payload" : {
				"any" : "payload",
				"goes" : "here""
			}
		}
	]
}
</pre>
<H3>JSon Request Object</H3>
    <DL>
        <DT>timeout</DT>
        <DD>Integer: Timeout in seconds for each individual request.</DD>
        <DT>queries</DT>
        <DD>Array: Individual calls to execute.
            <DL>
                <DT>id</DT>
                <DD>String: Unique identifier =used by client to correlate the query with the response.</DD>
                <DT>url</DT>
                <DD>URL: Target API to invoke, currently it will always be invoked with a POST.</DD>
                <DT>username</DT>
                <DD>Optional String: Userename for basic authentication to API.</DD>
                <DT>password</DT>
                <DD>Optional String: Password for basic authentication to API.</DD>
                <DT>payload</DT>
                <DD>JSon: Payload to be sent to the target API.  It can be a primitive or a compound json type.</DD>
            </DL>
        </DD>
    </DL>
"""
    return web.Response(text=text, content_type="text/html")


async def handler(request):
    req = await request.json()
    timeout = req["timeout"]
    tasks = []
    async with ClientSession() as session:
        for query in req["queries"]:
            task = asyncio.create_task(caller(session, query, timeout, request.headers.get('AUTHORIZATION')))
            tasks.append(task)
        queries = await asyncio.gather(*tasks)
    return web.json_response(queries)


async def caller(session, query, timeout, authtoken):
    result = {}
    result["start"] = datetime.now().isoformat(sep=" ", timespec="auto")
    id = query["id"]
    url = query["url"]
    payload = query["payload"]
    result["id"] = id
    headers = {}
    auth = None
    if "username" in query and "password" in query:
        auth = BasicAuth(login=query["username"],
                         password=query["password"])
    elif authtoken != None:
        headers["Authorization"] = authtoken
    try:
        async with session.post(url, json=payload, auth=auth, headers=headers, timeout=timeout) as response:
            if response.status < 200 or response.status > 299:
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
