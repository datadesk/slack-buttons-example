# Slack Buttons

A Flask app to document and test Slack's interactive messages.

## Getting Started

Create a virtualenv to store the codebase.
```bash
$ virtualenv slack_buttons
```

Activate the virtualenv.
```bash
$ cd slack_buttons
$ . bin/activate
```

Clone the git repository from GitHub.
```bash
$ git clone https://github.com/datadesk/slack-buttons-example.git repo
```

Enter the repo and install its dependencies.
```bash
$ cd repo
$ pip install -r requirements.txt
```

Fill in your Slack app's credentials in the [app](app.py#L11-L16) file.

Now run the test server and check out the results on localhost:5000
```bash
$ python app.py
```

## Testing Slack Buttons
This Flask app has three routes:
* '/': index is just to test to make sure the server is running
* '/test-add-story': test URL will post a test story in your Slack channel
* '/slack': webhook accepts POST requests from your Slack app after a button has been clicked
