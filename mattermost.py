import requests
import json
import time

from settings import secrets_mm

MATTERMOST_URL = secrets_mm['mm_url']
API_TOKEN = secrets_mm['mm_pymonitoring_apikey']


def retry(times=10, delay=60):
    def decorator(func):
        def f(*args, **kwargs):
            attempt = 0
            while attempt < times:

                response = func(*args, **kwargs)
                if response:
                    return response
                else:
                    print(f"{' '.join(time.asctime().split()[1:4])} > Connection error thrown when attempting to run {func} attempt")
                    attempt += 1
                    time.sleep(delay)

        return f

    return decorator


class Mattermost:

    def __init__(self):
        pass

    @retry()
    def mm_edit_helper_request(self, endpoint, headers, updated_post):

        response = requests.put(endpoint, json=updated_post, headers=headers, timeout=10)
        if response.status_code == 200:
            return response

        return 0

    @retry()
    def mm_get_post_helper_request(self, endpoint, headers):

        response = requests.get(endpoint, headers=headers)
        if response.status_code == 200:
            return response

        return 0

    @retry()
    def mm_post_helper_request(self, endpoint, headers, message_payload):

        response = requests.post(endpoint, headers=headers, data=json.dumps(message_payload))
        if response.status_code == 201:
            return response

        return 0

    def mm_edit(self, message, post_id, MATTERMOST_URL=MATTERMOST_URL, API_TOKEN=API_TOKEN):
        # Create a dictionary with the new post text
        updated_post = {
            'id': post_id,
            'message': message
        }

        # Define the API endpoint for updating a post
        endpoint = f'{MATTERMOST_URL}/posts/{post_id}'

        # Set the authorization header with the access token
        headers = {
            'Authorization': f'Bearer {API_TOKEN}',
            'Content-Type': 'application/json'
        }

        self.mm_edit_helper_request(endpoint, headers, updated_post)

    def mm_get_post(self, post_id, MATTERMOST_URL=MATTERMOST_URL, API_TOKEN=API_TOKEN):
        headers = {
            "Authorization": f"Bearer {API_TOKEN}",
            'Content-Type': 'application/json',
        }

        # Define the API endpoint for updating a post
        endpoint = f'{MATTERMOST_URL}/posts/{post_id}'

        response = self.mm_get_post_helper_request(endpoint, headers)

        if response.status_code == 200:
            post = response.json()
            message = post.get('message')
        else:
            return 503  # 503: Service Unavailable

        return message

    def mm_post(self, message, channel_id, MATTERMOST_URL=MATTERMOST_URL, API_TOKEN=API_TOKEN):
        # Create the headers with the authentication token
        headers = {
            'Authorization': f'Bearer {API_TOKEN}',
            'Content-Type': 'application/json',
        }

        # Define the API endpoint for updating a post
        endpoint = f'{MATTERMOST_URL}/posts'

        # Define the message payload
        message_payload = {
            'channel_id': channel_id,
            'message': message,
        }

        self.mm_post_helper_request(endpoint, headers, message_payload)

    def make_dict_from_mm(self, post_id):
        try:
            post = self.mm_get_post(post_id)

            lst = [x.strip().split(':') for x in post.split('\n') if
                   x != '"\n' and len(x) > 4]  # len(x) == 4 is an empty line

            out_dict = {}

            for pair in lst:
                out_dict.update({pair[0].strip('\''): float(pair[1].strip())})

        except ValueError:
            out_dict = {'Powiadomienia': 503}

        return out_dict
