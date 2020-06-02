# SplitJoin & Caching Microservice
[This image][DockerHub] receives a single REST request and splits it out into multiple parallel calls.
It then gathers the results and returns them as a single response.
Individual requests may be cached with a time to live.

This service takes a list of payloads and endpoints and sends the requests to all the endpoints in parallel.
It then collects the results and returns the results as a list of responses.
If a cachekey is specified then the cache is queried for previous results, if no previous result exists the query is executed and stored in the cache.

To call splitjoin **POST** to any URL on the splitjoin server.
The requirement to POST specifically to **/splitjoin** has been removed.

If a **GET** is done to any URL on the splitjoin server it will return this help.

This image is built on top of the [Python:3-slim] image.
A [github project][GitHub] contains the build instructions if a customized image is required.

## Authentication
Authentication has the following options:

* No Authentication  
    If no Authorization header is passed to the service and username/password are not specified in the query then the call is made without authentication  
* Query Specific Basic Authentication  
    If username and password are specified in the query then the call is made using basic authentication
* Pass Through Authentication  
    If no username/password are specified in the query and the request has an Authorization header then call is made using passed in authorization header.
    This allow the authentication to be passed through to the target API unchanged. 

## Caching
Individual request caching is supported using [redis] caching.  The redis cache is configured using environment variables:

* REDIS_HOST is the hostname of the redis server and must be provided to enable caching.
* REDIS_PORT is the optional port number of the redis server and defaults to the redis default port of 6379.
* REDIS_PASSWORD is the optional password of the redis server.

Caching is requested by providing a **cachekey** in the query.
An optional time to live in seconds is provided by the **cachettl** in the query.
Any cachekey is ignored if the **REDIS_HOST** is not set. 

## Logging
Logging can be enabled by the LOGGING environment variable.
Valid values are CRITICAL, ERROR, WARNING, INFO, DEBUG and NOTSET 

## Base Request Structure
Base request to service has following structure:

```json5

    {
        "timeout" : 30,
        "queries" : [
            {
                "id" : "id1",
                "url" : "https://server/path",
                "method" : "POST",
                "username" : "OptionalUsername",
                "password" : "OptionalPassword",
                "headers" : {
                    "header1" : "value1",
                    "header2" : "value2"
                },
                "payload" : {
                    "any" : "payload",
                    "goes" : "here"
                }
            },
            {
                "id" : "id2",
                "url" : "https://server/path",
                "payload" : {
                    "any" : "payload",
                    "goes" : "here"
                },
                "cachekey" : "recalls-2019-tesla",
                "cachettl" : 30
            },
            {
                "id" : "id3",
                "url" : "https://server/path",
                "method" : "GET",
                "params" : {
                    "param1" : "value1",
                    "param2" : "value2"
                }
            }
        ]
    }

```

### JSon Request Object
* timeout  
    Integer: Timeout in seconds for each individual request.
* queries    
    Array: Individual calls to execute.
    * id  
        String: Unique identifier used by client to correlate the query with the response.
    * url  
        URL: Target API to invoke, currently it will always be invoked with a POST.
    * method  
        Optional String: HTTP method.
    * username  
        Optional String: Userename for basic authentication to API.
    * password  
        Optional String: Password for basic authentication to API.
    * headers  
        Optional Dictionary: Collection of HTTP headers
        * header  
            String: Header name
        * value  
            String: Header value
    * payload  
        JSon: Payload to be sent to the target API.  It can be a primitive or a compound json type.
    * params  
        Optional Dictionary: Collection of HTTP Parameters
        * param  
            String: Param name
        * value  
            String: Param value
    * cachekey  
        Optional String: Key used to cache result.
        If not provided then the result ignores any cache.
    * cachettl  
        Optional Integer: Time to live in seconds.

## Response Structure
Response from service has following structure:

```json5

    [
        {
            "start": "2020-05-12 02:23:03.839570",
            "id": "id1",
            "response": {
                "any" : "response",
                "goes" : "here"
            },
            "headers": {
                "header1" : "value1",
                "header2" : "value2"
            },
            "status": 200,
            "end": "2020-05-12 02:23:27.597740"
        },
        {
            "start": "2020-05-12 02:23:03.843628",
            "id": "id2",
            "response": {
                "any" : "response",
                "goes" : "here"
            },
            "headers": {
                "header1" : "value1",
                "header2" : "value2"
            },
            "status": 200,
            "cached": "2020-06-02 05:34:46.675037",
            "end": "2020-05-12 02:23:30.594746"
        }
    ]

```

### JSon Response Object
* Array: Individual responses.
    * start  
        String: Date time call was made
    * id  
        String: Unique identifier used by client to correlate the response with the query.
    * response  
        JSon: Response received from the target API.  It can be a primitive or a compound json type.
    * headers  
        Dictionary: Received HTTP Headers
        * header  
            String: Header name
        * value  
            String: Header value
    * status  
        Integer: HTTP response code received from call
    * cached  
        String: Date time of request that was cached
    * end  
        String: Date time response was received

## Deployment
There are a number of ways to deploy the service:

* Run standalone using "python3 splitjoin.py".  Note that this requires [aiohttp], [redis][redis-py] and [markdown] packages.
* Run as a docker image using "docker run -p 8080:8080 docker.io/antonyjreynolds/splitjoin:latest"
* Run on a single node using docker-compose file  [docker-compose.yml] with redis cache server "docker-compose up".
* Deploy to Kubernetes using [deployment.yaml], if using Oracle OCI then the service deployment [service-oci-lb.yaml] will create a load balancer.

## Using with OIC
A sample package [Recalls.par] is provided that shows how to use splitjoin from OIC.
When setting up a connection to SplitJoin it is a good idea to set the security credentials to be OIC credentials.
This can be either Basic Auth or OAuth.
This will allow the SplitJoin to call OIC integrations without providing any additional credentials in the invoke.

## Test Suite
The provided [Postman] test suite [SplitJoin.postman_collection.json] can be used to verify an installation.
The environment file [SplitJoin Tests.postman_environment.json] can be configured to point to the SplitJoin server.
Note that if the cache is not enabled then some of the tests will fail.
Run the test suite twice within 30 seconds to see the effect of caching upon response times.
In tests running Splitjoin and redis locally on my iMac I saw response times drop from 130ms to 5ms with caching enabled.
 
[DockerHub]: https://hub.docker.com/r/antonyjreynolds/splitjoin
[GitHub]: https://github.com/AntonyJR/SplitJoin

[deployment.yaml]: https://raw.githubusercontent.com/AntonyJR/SplitJoin/master/deployment.yaml
[service-oci-lb.yaml]: https://raw.githubusercontent.com/AntonyJR/SplitJoin/master/service-oci-lb.yaml
[docker-compose.yml]: https://raw.githubusercontent.com/AntonyJR/SplitJoin/master/docker-compose.yml
[Recalls.par]: https://raw.githubusercontent.com/AntonyJR/SplitJoin/master/Recalls.par
[SplitJoin.postman_collection.json]: https://raw.githubusercontent.com/AntonyJR/SplitJoin/master/SplitJoin.postman_collection.json
[SplitJoin Tests.postman_environment.json]: https://raw.githubusercontent.com/AntonyJR/SplitJoin/master/SplitJoin%20Tests.postman_environment.json

[Python:3-slim]: https://hub.docker.com/_/python
[redis]: https://redis.io/
[Postman]: https://www.postman.com/

[redis-py]: https://pypi.org/project/redis/
[aiohttp]: https://docs.aiohttp.org
[markdown]: https://pypi.org/project/Markdown/
