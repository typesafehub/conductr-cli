from conductr_cli.constants import DEFAULT_AUTH_TOKEN_FILE
import os
try:
    import readline
except ImportError:
    import pyreadline as readline


AUTH_TOKEN_PROMPT = '\nAn access token is required. Please visit https://www.lightbend.com/account/access-token to \n' \
                    'obtain one, and a free license or your commercial one.\n' \
                    '\n' \
                    'Please enter your access token: '


def get_cached_auth_token():
    """
    Obtains cached token from local filesystem.
    :return: cached token
    """
    if os.path.exists(DEFAULT_AUTH_TOKEN_FILE):
        with open(DEFAULT_AUTH_TOKEN_FILE, 'r') as f:
            auth_token = f.readline()
    else:
        auth_token = None

    return auth_token


def prompt_for_auth_token():
    """
    Prompts for cached token from the user. Reads the token stdin keyed in by the user
    :return: cached token
    """
    readline.clear_history()

    try:
        return input(AUTH_TOKEN_PROMPT).strip()
    except EOFError:
        return ''


def remove_cached_auth_token():
    """
    Removes cached token from local filesystem.
    """
    if os.path.exists(DEFAULT_AUTH_TOKEN_FILE):
        os.remove(DEFAULT_AUTH_TOKEN_FILE)


def save_auth_token(auth_token):
    """
    Saves token into local filesystem.
    :param auth_token: The auth token to be saved.
    """
    os.makedirs(os.path.dirname(DEFAULT_AUTH_TOKEN_FILE), exist_ok=True)

    with open(DEFAULT_AUTH_TOKEN_FILE, 'w') as f:
        f.write(auth_token)
