import requests
import json
import time
import logging

from settings import secrets_mm

info_logger = logging.getLogger(__name__)
info_logger.setLevel(logging.INFO)
formatter_info = logging.Formatter('%(asctime)s >> %(message)s', datefmt='%Y-%m-%d %H:%M')
handler_info = logging.StreamHandler()
handler_info.setFormatter(formatter_info)
info_logger.addHandler(handler_info)

MATTERMOST_URL = secrets_mm['mm_url']
API_TOKEN = secrets_mm['mm_pymonitoring_apikey']


class Mattermost:

    def __init__(self):
        self.max_retries = 6
        self.retry_delay = 60

    def mm_edit_helper_request(self, endpoint, headers, updated_post):

        for retry_attempt in range(self.max_retries):
            try:
                response = requests.put(endpoint, json=updated_post, headers=headers, timeout=10)
                if response.status_code == 200:
                    return response

            # TODO very bad practice to catch all exceptions and don't even print/log what happened
            except Exception:
                info_logger.info('%s', 'Unable to edit post')
            time.sleep(self.retry_delay)

        return 0

    def mm_get_post_helper_request(self, endpoint, headers):
        for retry_attempt in range(self.max_retries):
            try:
                response = requests.get(endpoint, headers=headers)
                if response.status_code == 200:
                    return response
            except Exception:
                info_logger.info('%s', 'Unable to get post')
            time.sleep(self.retry_delay)

        return 0

    def mm_post_helper_request(self, endpoint, headers, message_payload):
        for retry_attempt in range(self.max_retries):
            try:
                response = requests.post(endpoint, headers=headers, data=json.dumps(message_payload))
                if response.status_code == 201:
                    return response
            except Exception:
                info_logger.info('%s', 'Unable to post')
            time.sleep(self.retry_delay)

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

        # Check if the request was successful.
        if response.status_code == 200:
            # Parse the JSON response to get the post details.
            post = response.json()
            message = post.get('message')
        else:
            raise ValueError()

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
            out_dict = {'Powiadomienia': 0}

        return out_dict
