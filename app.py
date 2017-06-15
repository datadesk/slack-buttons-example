#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Flask, request
from slack import http_client
from urllib import unquote_plus
import json
import re
app = Flask(__name__)

SLACK_BOT_TOKEN = ''
SLACK_VERIFICATION_TOKEN = ''

SLACK_CHANNEL = ''
SLACK_USERNAME = ''
SLACK_ICON = ''
SLACK_BUTTONS = [
    {
        'name': 'lead_story',
        'display': 'Lead',
        'value': 'True'
    },
    {
        'name': 'head_deck',
        'display': 'Head Deck',
        'value': 'True'
    },
    {
        'name': 'sidebar',
        'display': 'Side Bar',
        'value': 'True'
    }
]

fake_database = {
    'lead_story': {
        'la-robots-seen-as-boon-to-world': False
    },
    'head_deck': {
        'la-robots-seen-as-boon-to-world': False
    },
    'sidebar': {
        'la-robots-seen-as-boon-to-world': False
    }
}

def add_story(story):
    """
    Add a story message to our Slack channel.
    """
    attachments = [
        {
            'fallback': story['headline'],
            'title': '<'+story['url']+'|'+story['headline']+'>',
            'title_link': 'https//example.com/' + story['slug'],
            'thumb_url': story['thumbnail'],
            'callback_id': 'button_test',
            'actions': [],
            'fields': [
                {
                    'value': story['description']
                },
                {
                    'title': 'Slug',
                    'value': story['slug'],
                    'short': True
                },
                {
                    'title': 'Edit',
                    'value': '<https://example.com/edit/' + story['slug'] + '|Link>',
                    'short': True
                }
            ]
        }
    ]

    for button_dict in SLACK_BUTTONS:
        button = {
            'type':'button',
            'name':button_dict['name'],
            'text': '☐ ' + button_dict['display'],
            'value':button_dict['value'],
            'style':'danger',
        }
        attachments[0]['actions'].append(button)

    http_client.post(
        'chat.postMessage',
        dict(
            token=SLACK_BOT_TOKEN,
            channel=SLACK_CHANNEL,
            username=SLACK_USERNAME,
            icon_url=SLACK_ICON,
            text='',
            attachments=json.dumps(attachments)
        )
    )

def parse_request(request):
    """
    Parse the Slack POST request.
    """
    payload = request.get_data()
    payload = unquote_plus(payload)
    payload = re.sub('payload=','', payload)
    payload = json.loads(payload)
    return payload

def authorize(token):
    """
    Authorizes the webhook.
    """
    return token == SLACK_VERIFICATION_TOKEN

def update_message(payload):
    """
    Update a story's status in the databse and
    update the message in Slack to reflect it.
    """
    # Get the data you need from the payload.
    original_message = payload['original_message']
    story = original_message['attachments'][0]['fields'][1]['value']
    category = payload['actions'][0]['name']
    action_value = payload['actions'][0]['value']
    channel_id = payload['channel']['id']
    message_ts = payload['message_ts'] # serves as the message's Id
    username = payload['user']['name']

    # Run some code to update the story's category in your real database
    if action_value == 'True':
        fake_database[category][story] = True
    else:
        fake_database[category][story] = False


    # Get the story's status in each category.
    # You can't just reverse the status here because this app might not
    # be the only thing changing statuses.
    active_categories = get_statuses(story)

    # Make a new message
    new_message = dict(original_message) # This makes a copy of the old message to start with
    new_message['attachments'][0]['actions'] = [] # This resets the buttons
    for button in SLACK_BUTTONS:
        slug_name = button['name']
        status = not active_categories[button['name']]
        if status:
            style = 'danger'
            action_text = '☐ '
        else:
            style = 'primary'
            action_text = '☑ '
        text = action_text + button['display']

        button = {
            'name': slug_name,
            'text': text,
            'style': style,
            'type': 'button',
            'value': str(status)
        }
        new_message['attachments'][0]['actions'].append(button)

    http_client.post(
        'chat.update',
        dict(
            token=SLACK_BOT_TOKEN,
            username=SLACK_USERNAME,
            icon_url=SLACK_ICON,
            text='',
            channel=channel_id,
            ts=message_ts,
            attachments=json.dumps(new_message['attachments'])
        )
    )

    # Add a log of interactions to the message's thread
    thread_message = username + ' updated this story\'s status in ' + category + ' to ' + action_value
    http_client.post(
        'chat.postMessage',
        dict(
            token=SLACK_BOT_TOKEN,
            channel=channel_id,
            username=SLACK_USERNAME,
            icon_url=SLACK_ICON,
            text=thread_message,
            thread_ts=message_ts
        )
    )

    return ('', 202, None)

def get_statuses(slug):
    """
    Checks the status of a story in each category.
    """
    # Run some code to check the status of your story for each category
    # return a dictionary that has values for each button key
    statuses = {}
    for category in fake_database:
        statuses[category] = fake_database[category][slug]

    return statuses

@app.route('/', methods=['GET'])
def index():
    """
    Confirm that the server is working.
    """
    return ('This web app is working!')

@app.route('/slack', methods=['POST'])
def webhook():
    """
    Handle the webhook POST request and send it to the right action.
    """
    payload = parse_request(request)

    token = payload['token']
    if not authorize(token):
        return ('', 403, None)

    callback_id = payload['callback_id']
    if callback_id == 'button_test':
        return update_message(payload)

    return ('', 400, None)

@app.route('/test-add-story', methods=['GET'])
def test_add_story():
    new_story = {
        'headline':'Robots seen as boon to world',
        'url':'http://documents.latimes.com/robots-seen-boon-world/',
        'description':'On Feb. 26, 1928, the Los Angeles Times carried an article by R. J. Wensley, credited as the "inventor of the Mechanical Man," touting the potential for robotics to free humanity of the drudgery of work.',
        'slug': 'la-robots-seen-as-boon-to-world',
        'thumbnail': 'http://www.trbimg.com/img-59372291/turbine/la-robots-seen-as-boon-to-world-20170606/600'
    }
    add_story(new_story)
    return ('Robot Story Added.', 200, None)


if __name__ == '__main__':
    # Fire up the Flask test server
    app.run(debug=True, use_reloader=True)
