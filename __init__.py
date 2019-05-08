"""This module contains the Workbench food ordering blueprint application"""
from mindmeld import Application

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
            replies = ["All your applications are running normally."]
        responder.frame = {}
    else:
        replies = ["I'm sorry, you didn't specify the resource."]   
     
    responder.reply(replies)