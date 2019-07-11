from mindmeld import Application
import requests
import json
import urllib3
import time


from urllib3.exceptions import InsecureRequestWarning  # for insecure https warnings
from requests.auth import HTTPBasicAuth  # for Basic Auth

urllib3.disable_warnings(InsecureRequestWarning)  # disable insecure https warnings

app = Application(__name__)

__all__ = ['app']

ip = {
        "router": "10.10.22.74",
        "core-switch": "10.10.22.73",
        "access-switch-1": "10.10.22.66",
        "access-switch-2": "10.10.22.70",
        "server-1": "10.10.22.98",
        "server-2": "10.10.22.114"
    }

dev = {
        "10.10.22.74": "Border Router",
        "10.10.22.73": "Core Switch",
        "10.10.22.66": "Access Switch 1",
        "10.10.22.70": "Access Switch 2",
        "10.10.22.98": "Server 1",
        "10.10.22.114": "Server 2"
    }


@app.handle(default=True)
@app.handle(intent='unsupported')
def default(request, responder):
    """
    When the user asks an unrelated question, convey the lack of understanding for the requested
    information and prompt to return to food ordering.
    """
    reply = "Sorry, not sure what you meant there. I can help you to obtain information about the status of your applications and your network, to perform path traces and to open support tickets."
    responder.reply(text=reply)
    responder.speak(text=reply)


@app.handle(intent='greet')
def welcome(request, responder):
    """
    When the user starts a conversation, say hi and give some restaurant suggestions to explore.
    """
    try:
        # Get user's name from session information in a request to personalize the greeting.
        responder.slots['name'] = request.context['name']
        prefix = 'Hello, {name}. '
    except KeyError:
        prefix = 'Hello. '

    # Build up the final natural language response and reply to the user.
    responder.reply(prefix + 'I can help you to obtain information about the status of your applications and your network, to perform path traces and to open support tickets.')
    responder.speak(prefix + 'I can help you to obtain information about the status of your applications and your network, to perform path traces and to open support tickets.')


@app.handle(intent='exit')
def say_goodbye(request, responder):
    """
    When the user ends a conversation, clear the dialogue frame and say goodbye.
    """
    # Clear the dialogue frame to start afresh for the next user request.
    responder.frame = {}

    # Respond with a random selection from one of the canned "goodbye" responses.
    responder.reply(['Bye!', 'Goodbye!', 'Have a nice day.', 'See you later.'])
    responder.speak(['Bye!', 'Goodbye!', 'Have a nice day.', 'See you later.'])


@app.handle(intent='help')
def provide_help(request, responder):
    """
    When the user asks for help, provide some sample queries they can try.
    """
    reply = "I can help you to obtain information about the status of your applications and your network, to perform path traces and to open support tickets."
    responder.reply(text=reply)
    responder.speak(text=reply)


@app.handle(intent='start_over')
def start_over(request, responder):
    """
    When the user wants to start over, clear the dialogue frame and reply for the next request.
    """
    # Clear the dialogue frame and respond with a variation of the welcome message.
    responder.frame = {}
    replies = ["Ok, let's start over! What restaurant would you like to order from?"]
    responder.reply(replies)
    responder.listen()


@app.handle(intent='do-path-trace')
def path_trace(request, responder):
    src = next((e for e in request.entities if e['role'] == 'source'), None)
    if src:
        src = src['value'][0]['cname']
        responder.frame['source_device'] = src
    dest = next((e for e in request.entities if e['role'] == 'destination'), None)
    if dest:
        dest = dest['value'][0]['cname']
        responder.frame['destination_device'] = dest

    if src and dest:
        dnac_token = get_dnac_jwt_token(DNAC_AUTH)
        path_id = create_path_trace(ip[src], ip[dest], dnac_token)
        time.sleep(0.5)
        trace = get_path_trace_info(path_id, dnac_token)
        graph_url = "http://localhost:5000/graphs"
        payload = {"graph_type": "dnac",
                "trace": trace
                }
        headers = {"Content-Type": "application/json"}
        response = requests.request("POST", graph_url, data=json.dumps(payload), headers=headers)
        graph_url = response.text
        payload = {"url": graph_url}
        reply = "Here is the path trace you requested."
    else:
        graph_url = "http://localhost:5000/graphs"
        payload = {"graph_type": "network_diagram"}
        headers = {"Content-Type": "application/json"}
        response = requests.request("POST", graph_url, data=json.dumps(payload), headers=headers)
        graph_url = response.text
        payload = {"url": graph_url}
        
        if src and not dest:
            responder.frame['source_device'] = src
            responder.params.allowed_intents = ['do_path_trace_followup']
            reply = "Here is a network diagram. To what destination do you want to perform the trace?"
        elif not src and dest:
            responder.frame['destination_device'] = dest
            responder.params.allowed_intents = ['do_path_trace_followup']
            reply = "Here is a network diagram. From what device do you want to perform the trace"
        else:
            responder.params.allowed_intents = ['do-path-trace']
            reply = "Here is a network diagram. Please specify the source and destination devices for the trace"

    responder.act("display-web-view", payload=payload)
    responder.reply(text=reply)
    responder.speak(text=reply)
    responder.act('sleep')

@app.handle(intent='do-path-trace-followup')
def do_path_trace_followup(request, responder):
    print(request.entities)
    print(request.frame['destination_device'])
    print(request.frame['source_device'])
    try:
        src = request.frame['source_device']
    except:
        src = None
    try:
        dest = request.frame['destination_device']
    except:
        dest = None

    if not src:
        src = next((e for e in request.entities if e['type'] == 'device'), None)
        src = src['value'][0]['cname']
    elif not dest:
        dest = next((e for e in request.entities if e['type'] == 'device'), None)
        dest = dest['value'][0]['cname']

    if src and dest:
        dnac_token = get_dnac_jwt_token(DNAC_AUTH)
        path_id = create_path_trace(ip[src], ip[dest], dnac_token)
        time.sleep(0.5)
        trace = get_path_trace_info(path_id, dnac_token)
        graph_url = "http://localhost:5000/graphs"
        payload = {"graph_type": "dnac",
                "trace": trace
                }
        headers = {"Content-Type": "application/json"}
        response = requests.request("POST", graph_url, data=json.dumps(payload), headers=headers)
        graph_url = response.text
        payload = {"url": graph_url}
        reply = "Here is the path trace you requested."
    else:
        graph_url = "http://localhost:5000/graphs"
        payload = {"graph_type": "network_diagram"}
        headers = {"Content-Type": "application/json"}
        response = requests.request("POST", graph_url, data=json.dumps(payload), headers=headers)
        graph_url = response.text
        payload = {"url": graph_url}
        responder.params.allowed_intents = ['do-path-trace']
        reply = "Here is a network diagram. Please specify the source and destination devices for the trace"
 
    responder.act("display-web-view", payload=payload)
    responder.reply(text=reply)
    responder.speak(text=reply)
    responder.act('sleep')
    

    
    


@app.handle(intent='open-ticket')
def open_ticket(request, responder):

    # Set the request parameters
    url = 'https://dev49204.service-now.com/api/now/table/incident'

    # Eg. User name="admin", Password="admin" for this code sample.
    user = 'admin'
    pwd = 'Cisco123!'

    # Set proper headers
    headers = {"Content-Type":"application/json","Accept":"application/json"}

    # Do the HTTP request
    response = requests.post(url, auth=(user, pwd), headers=headers ,data="{\"short_description\":\"There's a problem with the application MyNodeApp.\",\"category\":\"Network\",\"subcategory\":\"Application Performance\",\"description\":\"The threshold of 3000 requests per second was surpassed during the last hour. Requests per minute graph: https://clus-demo.altus.cr/graphs/static/31fae0d03c5740269d8a729f48c2c875.html\",\"caller_id\":\"webexassistant\"}")

    # Check for HTTP codes other than 200
    if response.status_code != 200: 
        #print('Status:', response.status_code, 'Headers:', response.headers, 'Error Response:',response.json())
        print("Success!!!")
    # Decode the JSON response into a dictionary and use the data
    data = response.json()
    ticket_number = data['result']['number']
    responder.slots['ticket_number'] = ticket_number
    graph_url = "http://localhost:5000/graphs"
    payload = {"graph_type": "service_now",
               "ticket_number": ticket_number
            }
    headers = {"Content-Type": "application/json"}
    response = requests.request("POST", graph_url, data=json.dumps(payload), headers=headers)
    graph_url = response.text
    payload = {"url": graph_url}
    reply = "Your ticket number is {ticket_number}."    

    responder.act("display-web-view", payload=payload)
    responder.reply(text=reply)
    responder.speak(text=reply)
    responder.act('sleep')

    
@app.handle(intent='show-resource-status')
def resource_status(request, responder):

    resource = [e for e in request.entities if e['type'] == 'resource']

    if resource:
        resource = resource[0]['value'][0]['cname']
        if resource == "network":
            replies = ["There's a problem with you network."]
        elif resource == "applications":
            if health_rule_violation():
                graph_url = get_calls_per_min()
                payload = {"url": graph_url}
                reply = "There's an issue with your application. Here is a graph of your application's performance over the last 60 minutes."
            else:
                graph_url = get_app_perf()
                payload = {"url": graph_url}
                reply = "All your applications are running normally. Here is a graph of your application's performance over the last 60 minutes."
        responder.frame = {}
    else:
        reply = "I'm sorry, you didn't specify the resource."
     
    responder.act("display-web-view", payload=payload)
    responder.reply(text=reply)
    responder.speak(text=reply)
    responder.act('sleep')

def get_app_perf():

    appd_url = "https://altusconsulting.saas.appdynamics.com/controller/rest/applications/MyNodeApp/metric-data"
    querystring = {"rollup":"false","metric-path":"Overall Application Performance|Average Response Time (ms)","time-range-type":"BEFORE_NOW","duration-in-mins":"60","output":"JSON"}
    payload = ""
    headers = {
        'Authorization': "Bearer eyJraWQiOiIxIiwiYWxnIjoiSFMyNTYifQ.eyJpc3MiOiJBcHBEeW5hbWljcyIsImF1ZCI6IkFwcERfQVBJcyIsImV4cCI6MTU4ODg4MzQ4OSwianRpIjoiVXdtdnBtMGF3ZHVCQW9UbHM5WGMwdyIsImlhdCI6MTU1NzM0NzQ4OSwibmJmIjoxNTU3MzQ3MzY5LCJzdWIiOiJhcGl1c2VyIiwidHlwZSI6IkFQSV9DTElFTlQiLCJpZCI6ImI4OWJlNGJhLTVmYmMtNDJkYy1hNzU2LThjZDRlZTBlNDdjZiIsImFjY3RJZCI6ImIwYmJmMDZkLTZlZDMtNDI4YS1hYTgwLThkMDMwODI0NzNhYiIsImFjY3ROYW1lIjoiYWx0dXNjb25zdWx0aW5nIn0.PMKUS5bwHpgWwMwmpp5IO4As56IW52yp5Xm8URWoNw0",
        'Accept': "*/*",
        'Host': "altusconsulting.saas.appdynamics.com",
        'cache-control': "no-cache"
        }
    response = requests.request("GET", appd_url, data=payload, headers=headers, params=querystring)
    metrics = response.json()
    metrics = metrics[0]["metricValues"]
    values = []
    for metric in metrics:
        value = metric["value"]
        values.append(value)
    
    graph_url = "http://localhost:5000/graphs"
    payload = {"graph_type": "appd",
               "data": values,
	           "graph_label": "'Overall Application Performance|Average Response Time (ms)'",
	           "app_name": "MyNodeApp",
	           "vertical_axis_label": "'Response Time (ms)'"
            }
    headers = {"Content-Type": "application/json"}
    response = requests.request("POST", graph_url, data=json.dumps(payload), headers=headers)
    return response.text
    

def health_rule_violation():

    appd_url = "https://altusconsulting.saas.appdynamics.com/controller/rest/applications/49309/events"
    querystring = {"output":"JSON","time-range-type":"BEFORE_NOW","duration-in-mins":"60","event-types":"APPLICATION_ERROR,APP_SERVER_RESTART,APPLICATION_CONFIG_CHANGE,POLICY_OPEN_CRITICAL","severities":"INFO,WARN,ERROR"}
    payload = ""
    headers = {
        'Authorization': "Bearer eyJraWQiOiIxIiwiYWxnIjoiSFMyNTYifQ.eyJpc3MiOiJBcHBEeW5hbWljcyIsImF1ZCI6IkFwcERfQVBJcyIsImV4cCI6MTU4ODg4MzQ4OSwianRpIjoiVXdtdnBtMGF3ZHVCQW9UbHM5WGMwdyIsImlhdCI6MTU1NzM0NzQ4OSwibmJmIjoxNTU3MzQ3MzY5LCJzdWIiOiJhcGl1c2VyIiwidHlwZSI6IkFQSV9DTElFTlQiLCJpZCI6ImI4OWJlNGJhLTVmYmMtNDJkYy1hNzU2LThjZDRlZTBlNDdjZiIsImFjY3RJZCI6ImIwYmJmMDZkLTZlZDMtNDI4YS1hYTgwLThkMDMwODI0NzNhYiIsImFjY3ROYW1lIjoiYWx0dXNjb25zdWx0aW5nIn0.PMKUS5bwHpgWwMwmpp5IO4As56IW52yp5Xm8URWoNw0",
        'Accept': "*/*",
        'Host': "altusconsulting.saas.appdynamics.com",
        'cache-control': "no-cache"
        }
    response = requests.request("GET", appd_url, data=payload, headers=headers, params=querystring)
    events = response.json()
    health_rule_violation = False
    if len(events) > 0:
        for event in events:
            if event["type"] == "POLICY_OPEN_CRITICAL":
                health_rule_violation = True
    #return health_rule_violation  - Workaround while the AppD API issue is fixed.
    return True


def get_calls_per_min():

    # appd_url = "https://altusconsulting.saas.appdynamics.com/controller/rest/applications/MyNodeApp/metric-data"
    # querystring = {"output":"JSON","rollup":"false","metric-path":"Overall Application Performance|Calls per Minute","time-range-type":"BEFORE_NOW","duration-in-mins":"60"}
    # payload = ""
    # headers = {
    #     'Authorization': "Bearer eyJraWQiOiIxIiwiYWxnIjoiSFMyNTYifQ.eyJpc3MiOiJBcHBEeW5hbWljcyIsImF1ZCI6IkFwcERfQVBJcyIsImV4cCI6MTU4ODg4MzQ4OSwianRpIjoiVXdtdnBtMGF3ZHVCQW9UbHM5WGMwdyIsImlhdCI6MTU1NzM0NzQ4OSwibmJmIjoxNTU3MzQ3MzY5LCJzdWIiOiJhcGl1c2VyIiwidHlwZSI6IkFQSV9DTElFTlQiLCJpZCI6ImI4OWJlNGJhLTVmYmMtNDJkYy1hNzU2LThjZDRlZTBlNDdjZiIsImFjY3RJZCI6ImIwYmJmMDZkLTZlZDMtNDI4YS1hYTgwLThkMDMwODI0NzNhYiIsImFjY3ROYW1lIjoiYWx0dXNjb25zdWx0aW5nIn0.PMKUS5bwHpgWwMwmpp5IO4As56IW52yp5Xm8URWoNw0",
    #     'Accept': "*/*",
    #     'Host': "altusconsulting.saas.appdynamics.com",
    #     'cache-control': "no-cache"
    #     }
    # response = requests.request("GET", appd_url, data=payload, headers=headers, params=querystring)
    # metrics = response.json()
    # metrics = metrics[0]["metricValues"]
    # values = []
    # for metric in metrics:
    #     value = metric["value"]
    #     values.append(value)

    #Workaround while the AppD API issue is fixed
    values = [
        1643,
        1441,
        1391,
        1369,
        1390,
        1545,
        1653,
        1575,
        1463,
        1333,
        1435,
        1453,
        1310,
        1469,
        1515,
        2551,
        3362,
        3217,
        2111,
        1310,
        1294,
        1387,
        1336,
        1328,
        1550,
        1504,
        1482,
        1626,
        1680,
        1611,
        1558,
        1423,
        1488,
        1449,
        1318,
        1488,
        1517,
        1372,
        1383,
        1571,
        1611,
        1560,
        1626,
        1545,
        1572,
        1579,
        1401,
        1351,
        1445,
        1597,
        1679,
        1580,
        1337,
        1297,
        1510,
        1456,
        1417,
        1467,
        1374,
        1516,
    ]
    graph_url = "http://localhost:5000/graphs"
    payload = {"graph_type": "appd",
               "data": values,
	           "graph_label": "'Overall Application Performance|Calls per Minute'",
	           "app_name": "MyNodeApp",
	           "vertical_axis_label": "'Calls per Minute'"
            }
    headers = {"Content-Type": "application/json"}
    response = requests.request("POST", graph_url, data=json.dumps(payload), headers=headers)
    return response.text

DNAC_AUTH = HTTPBasicAuth("devnetuser", "Cisco123!")
#DNAC_URL = "https://sandboxdnac.cisco.com"
DNAC_URL = "http://localhost:5001"

def get_dnac_jwt_token(dnac_auth):
    """
    Create the authorization token required to access DNA C
    Call to DNA C - /api/system/v1/auth/login
    :param dnac_auth - DNA C Basic Auth string
    :return: DNA C JWT token
    """

    url = DNAC_URL + '/api/system/v1/auth/login'
    header = {'content-type': 'application/json'}
    response = requests.get(url, auth=dnac_auth, headers=header, verify=False)
    response_header = response.headers
    dnac_jwt_token = response_header['Set-Cookie']

    # with open('../dnac_token_request/dnac_token.cfg', 'r') as filehandle:  
    #         dnac_jwt_token = filehandle.read()

    return dnac_jwt_token


def create_path_trace(src_ip, dest_ip, dnac_jwt_token):
    """
    This function will create a new Path Trace between the source IP address {src_ip} and the
    destination IP address {dest_ip}
    :param src_ip: Source IP address
    :param dest_ip: Destination IP address
    :param dnac_jwt_token: DNA C token
    :return: DNA C path visualisation id
    """

    param = {
        'destIP': dest_ip,
        'periodicRefresh': False,
        'sourceIP': src_ip
    }

    url = DNAC_URL + '/api/v1/flow-analysis'
    header = {'accept': 'application/json', 'content-type': 'application/json', 'Cookie': dnac_jwt_token}
    path_response = requests.post(url, data=json.dumps(param), headers=header, verify=False)
    path_json = path_response.json()
    path_id = path_json['response']['flowAnalysisId']
    return path_id


def get_path_trace_info(path_id, dnac_jwt_token):
    """
    This function will return the path trace details for the path visualisation {id}
    :param path_id: DNA C path visualisation id
    :param dnac_jwt_token: DNA C token
    :return: Path visualisation status, and the details in a list [device,interface_out,interface_in,device...]
    """

    url = DNAC_URL + '/api/v1/flow-analysis/' + path_id
    header = {'accept': 'application/json', 'content-type': 'application/json', 'Cookie': dnac_jwt_token}
    path_response = requests.get(url, headers=header, verify=False)
    path_json = path_response.json()
    path_info = path_json['response']
    path_status = path_info['request']['status']
    path_list = []
    if path_status == 'COMPLETED':
        network_info = path_info['networkElementsInfo']
        for elem in network_info:
            path_list.append({"type": simplify_type(elem["type"]),
                              "ip": elem["ip"],
                              "name": dev[elem["ip"]]
                              })

    return path_list


def simplify_type(type):
    if type == "Routers":
        return "router"
    elif type == "Switches and Hubs":
        return "switch"
    elif type == "wired":
        return "server"
    else:
        return "unknown"
