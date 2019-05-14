"""This module contains the Workbench food ordering blueprint application"""
from mindmeld import Application
import requests
import json

app = Application(__name__)

__all__ = ['app']


@app.handle(default=True)
@app.handle(intent='unsupported')
def default(request, responder):
    """
    When the user asks an unrelated question, convey the lack of understanding for the requested
    information and prompt to return to food ordering.
    """
    replies = ["Sorry, not sure what you meant there. I can help you to obtain information about the status of your applications and your network, to perform path traces and to open support tickets."]
    responder.reply(replies)


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

@app.handle(intent='exit')
def say_goodbye(request, responder):
    """
    When the user ends a conversation, clear the dialogue frame and say goodbye.
    """
    # Clear the dialogue frame to start afresh for the next user request.
    responder.frame = {}

    # Respond with a random selection from one of the canned "goodbye" responses.
    responder.reply(['Bye!', 'Goodbye!', 'Have a nice day.', 'See you later.'])


@app.handle(intent='help')
def provide_help(request, responder):
    """
    When the user asks for help, provide some sample queries they can try.
    """
    replies = ["I can help you to obtain information about the status of your applications and your network, to perform path traces and to open support tickets."]
    responder.reply(replies)


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

    replies = ["Performing a path trace..."]        
    responder.reply(replies)


@app.handle(intent='open-ticket')
def open_ticket(request, responder):

    replies = ["Opening a support ticket..."]        
    responder.reply(replies)

    
@app.handle(intent='show-resource-status')
def resource_status(request, responder):

    resource = [e for e in request.entities if e['type'] == 'resource']

    if resource:
        resource = resource[0]['value'][0]['cname']
        if resource == "network":
            replies = ["There's a problem with you network."]
        elif resource == "applications":
            graph_url = get_app_perf()
            payload = {"text": "All your applications are running normally. Here is a graph of your application's performance over the last 60 minutes.", "url": graph_url}
        responder.frame = {}
    else:
        replies = ["I'm sorry, you didn't specify the resource."]   
     
    #responder.reply(replies)
    responder.act("display-web-view", payload=payload)

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
    payload = {"data": values,
	           "graph_label": "'Overall Application Performance|Average Response Time (ms)'",
	           "app_name": "'MyNodeApp Application Status'",
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
    response = requests.request("GET", url, data=payload, headers=headers, params=querystring)
    events = response.json()
    health_rule_violation = False
    if events.len() > 0:
        for event in events:
            if event["type"] == "POLICY_OPEN_CRITICAL":
                health_rule_violation = True
    return health_rule_violation


def get_calls_per_min():

    appd_url = "https://altusconsulting.saas.appdynamics.com/controller/rest/applications/MyNodeApp/metric-data"
    querystring = {"rollup":"false","metric-path":"Overall Application Performance|Calls per Minute","time-range-type":"BEFORE_NOW","duration-in-mins":"60"}
    payload = ""
    headers = {
        'Authorization': "Bearer eyJraWQiOiIxIiwiYWxnIjoiSFMyNTYifQ.eyJpc3MiOiJBcHBEeW5hbWljcyIsImF1ZCI6IkFwcERfQVBJcyIsImV4cCI6MTU4ODg4MzQ4OSwianRpIjoiVXdtdnBtMGF3ZHVCQW9UbHM5WGMwdyIsImlhdCI6MTU1NzM0NzQ4OSwibmJmIjoxNTU3MzQ3MzY5LCJzdWIiOiJhcGl1c2VyIiwidHlwZSI6IkFQSV9DTElFTlQiLCJpZCI6ImI4OWJlNGJhLTVmYmMtNDJkYy1hNzU2LThjZDRlZTBlNDdjZiIsImFjY3RJZCI6ImIwYmJmMDZkLTZlZDMtNDI4YS1hYTgwLThkMDMwODI0NzNhYiIsImFjY3ROYW1lIjoiYWx0dXNjb25zdWx0aW5nIn0.PMKUS5bwHpgWwMwmpp5IO4As56IW52yp5Xm8URWoNw0",
        'Accept': "*/*",
        'Host': "altusconsulting.saas.appdynamics.com",
        'cache-control': "no-cache"
        }
    response = requests.request("GET", url, data=payload, headers=headers, params=querystring)

