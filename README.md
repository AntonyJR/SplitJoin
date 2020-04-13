# SplitJoin Microservice
Receive a single REST request and split it out into multiple parallel calls.
Then gather results and return them as a single response.

This service takes a list of payloads and endpoints and sends the requests to all the endpoints in parallel.
It then collects the results and returns the results as a list of responses.

To call splitjoin **POST** to URL **/splitjoin**

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
	    		}
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

### JSon Request Object

**timeout**  
Integer: Timeout in seconds for each individual request.

**queries**  
Array: Individual calls to execute.

    **id**  
        String: Unique identifier =used by client to correlate the query with the response.

    **url**  
        URL: Target API to invoke, currently it will always be invoked with a POST.

    **method**  
        Optional String: HTTP method.

    **username**  
        Optional String: Userename for basic authentication to API.

    **password**  
        Optional String: Password for basic authentication to API.

    **headers**  
        Optional Dictionary: Collection of HTTP headers

        **header**  
            String: Header name

        **value**  
            String: Header value

    **payload**  
        JSon: Payload to be sent to the target API.  It can be a primitive or a compound json type.
