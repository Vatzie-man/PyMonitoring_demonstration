import requests
import json
import time

from settings import secrets_mm

MATTERMOST_URL = secrets_mm['mm_url']
API_TOKEN = secrets_mm['mm_pymonitoring_apikey']

# MonitorChannels class:
MM_ACCESS_TOKEN = secrets_mm["WK_ACCESS_TOKEN"]
WACLAW_CHANNEL = secrets_mm["WACLAW_CHANNEL"]
DTP_CHANNEL = secrets_mm["DTP_CHANNEL"]
INFRASTRUKTURA_CHANNEL = secrets_mm["PYCHOWICE_INFRASTRUKTURA_CHANNEL"]

# CHANNELS_IDs = {WACLAW_CHANNEL: None, DTP_CHANNEL: None, INFRASTRUKTURA_CHANNEL: None}
CHANNELS_IDs = {DTP_CHANNEL: None, INFRASTRUKTURA_CHANNEL: None}
CHANNELS_NAMES = {WACLAW_CHANNEL: 'WACLAW', DTP_CHANNEL: 'DTP', INFRASTRUKTURA_CHANNEL: 'INFRASTRUKTURA'}

def retry(times=20, delay=30):
    def decorator(func):
        def f(*args, **kwargs):
            attempt = 0
            while attempt < times:

                response = func(*args, **kwargs)
                if response:
                    return response
                else:
                    print(f"{' '.join(time.asctime().split()[1:4])} > Error running {func}.")
                    attempt += 1
                    time.sleep(delay)

        return f

    return decorator


class Mattermost:
    def __init__(self):
        pass

    @retry()
    def mm_edit_helper_request(self, endpoint, headers, updated_post):

        try:
            response = requests.put(endpoint, json=updated_post, headers=headers, timeout=10)
            if response.status_code == 200:
                return response
            return 0
        except Exception:
            return 0

    @retry()
    def mm_get_post_helper_request(self, endpoint, headers):

        try:
            response = requests.get(endpoint, headers=headers)
            if response.status_code == 200:
                return response
            return 0
        except Exception:
            return 0

    @retry()
    def mm_post_helper_request(self, endpoint, headers, message_payload):

        try:
            response = requests.post(endpoint, headers=headers, data=json.dumps(message_payload))
            if response.status_code == 201:
                return response
            return 0
        except Exception:
            return 0

    def mm_edit(self, message, post_id, API_TOKEN=API_TOKEN, MATTERMOST_URL=MATTERMOST_URL):
        '''Create a dictionary with the new post text'''
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
        '''Fetch post'''
        headers = {
            "Authorization": f"Bearer {API_TOKEN}",
            'Content-Type': 'application/json',
        }

        # Define the API endpoint for updating a post
        endpoint = f'{MATTERMOST_URL}/posts/{post_id}'

        response = self.mm_get_post_helper_request(endpoint, headers)

        if response:
            post = response.json()
            message = post.get('message')
        else:
            return 503  # 503: Service Unavailable

        return message

    def mm_post(self, message, channel_id, MATTERMOST_URL=MATTERMOST_URL, API_TOKEN=API_TOKEN):
        '''Create the headers with the authentication token'''
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
        '''Makes dict from fetched text for settings in out_of_tolerance'''
        try:
            post = self.mm_get_post(post_id)

            lst = [x.strip().split(':') for x in post.split('\n') if
                   x != '"\n' and len(x) > 4]  # len(x) == 4 is an empty line

            out_dict = {}

            for pair in lst:
                out_dict.update({pair[0].strip('\''): float(pair[1].strip())})

        except Exception:
            out_dict = {'Powiadomienia': 503}

        return out_dict

class MonitorChannels():
    '''Monitors Mattermost channels for new messages'''
    def __init__(self):

        self.headers = {
            "Authorization": f"Bearer {MM_ACCESS_TOKEN}",
            'Content-Type': 'application/json',
        }
        self.first_program_run: bool = True

    def set_first_program_run(self) -> None:
        self.first_program_run = False

    @retry()
    def read_post_helper(self, url):
        try:
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                return response
            return 0
        except Exception:
            return 0

    @retry()
    def new_messages_helper(self, url):
        try:
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                return response
            return 0
        except Exception:
            return 0

    def read_post(self, post_id):

        url = f'{MATTERMOST_URL}/posts/{post_id}'

        response = self.read_post_helper(url)

        if response:
            post = response.json()
            message = post.get('message')
            return message
        else:
            return "Can't read post."

    def get_new_messages(self):
        new_message = []
        for k, v in CHANNELS_IDs.items():
            url = f"{MATTERMOST_URL}/channels/{k}/posts"

            response = self.new_messages_helper(url)

            if response:
                post = response.json()['order'][0]  # get newest post
                time.sleep(1)
                message = self.read_post(post)

                if (v != message) and (message != ''):
                    new_message.append(f"{CHANNELS_NAMES[k]}: {message}")
                CHANNELS_IDs[k] = message
            else:
                return "Can't read channel."

        if self.first_program_run:
            self.set_first_program_run()
            return []

        else:
            return new_message[0] if new_message else ''


# out = MonitorChannels()
# out.get_new_messages()