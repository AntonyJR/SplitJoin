# SplitJoin Microservice
[This image][DockerHub] receives a single REST request and splits it out into multiple parallel calls.
It then gathers the results and returns them as a single response.

This service takes a list of payloads and endpoints and sends the requests to all the endpoints in parallel.
It then collects the results and returns the results as a list of responses.

To call splitjoin **POST** to URL **/splitjoin**

This image is built on top of the [Python:3-slim] image.
A [github project][GitHub] contains the build instructions if a customized image is required.

## Authentication
Authentication has the following options:
+ No Authentication  
    If no Authorization header is passed to the service and username/password are not specified in the query then the call is made without authentication  
+ Query Specific Basic Authentication  
    If username and password are specified in the query then the call is made using basic authentication
+ Pass Through Authentication  
    If no username/password are specified in the query and the request has an Authorization header then call is made using passed in authorization header.
    This allow the authentication to be passed through to the target API unchanged. 

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
            }
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
    timeout  
        Integer: Timeout in seconds for each individual request.
    queries    
        Array: Individual calls to execute.
            id  
                String: Unique identifier =used by client to correlate the query with the response.
            url  
                URL: Target API to invoke, currently it will always be invoked with a POST.
            method  
                Optional String: HTTP method.
            username  
                Optional String: Userename for basic authentication to API.
            password  
                Optional String: Password for basic authentication to API.
            headers  
                Optional Dictionary: Collection of HTTP headers
                    header  
                        String: Header name
                    value
                        String: Header value
            payload
                JSon: Payload to be sent to the target API.  It can be a primitive or a compound json type.
            params
                Optional Dictionary: Collection of HTTP Parameters
                    param
                        String: Param name
                    value
                        String: Param value

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
        "status": 200,
        "end": "2020-05-12 02:23:30.594746"
    }
]
```

### JSon Response Object
    Array: Individual responses.
        start
            String: Date time call was made
        id  
            String: Unique identifier used by client to correlate the response with the query.
        response
            JSon: Response received from the target API.  It can be a primitive or a compound json type.
        status:
            Integer: HTTP response code received from call
        end
            String: Date time response was received

## Deployment
There are a number of ways to deploy the service:
* Run standalone using "python3 splitjoin.py".  Note that this requires [aiohttp] package.
* Run as a docker image using "docker run -p 8080:8080 docker.io/antonyjreynolds/splitjoin:latest"
* Deploy to Kubernetes using [deployment.yaml], if using Oracle OCI then the service deployment [service-oci-lb.yaml] will create a load balancer.

## Using with OIC
A sample package [Recalls.par] is provided that shows how to use splitjoin from OIC.
When setting up a connection to SplitJoin it is a good idea to set the security credentials to be OIC credentials.
This can be either Basic Auth or OAuth.
This will allow the SplitJoin to call OIC integrations without providing any additional credentials in the invoke.

[Python:3-slim]: https://hub.docker.com/_/python
[DockerHub]: https://hub.docker.com/r/antonyjreynolds/splitjoin
[GitHub]: https://github.com/AntonyJR/SplitJoin
[deployment.yaml]: https://raw.githubusercontent.com/AntonyJR/SplitJoin/master/deployment.yaml
[service-oci-lb.yaml]: https://raw.githubusercontent.com/AntonyJR/SplitJoin/master/service-oci-lb.yaml
[aiohttp]: https://docs.aiohttp.org
[Recalls.par]: https://raw.githubusercontent.com/AntonyJR/SplitJoin/master/Recalls.par
