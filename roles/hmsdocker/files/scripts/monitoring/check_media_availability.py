#!/usr/bin/env python3

# This script is meant to be ran as a cron job on the same host that is running plex
# If pointed to an external host, I cannot guarantee the security as SSL verification is disabled in this script on purpose

# This script monitors the case when Plex is running but the network share was not mounted correctly, resulting in an available server but no available media


## REQUIRED BY SNYK, DO NOT REMOVE
# file deepcode ignore SSLVerificationBypass: plex localhost serves self-signed cert by default

import requests
import logging
import os
import sys
from dotenv import load_dotenv
import xmltodict

import urllib3
urllib3.disable_warnings()

logger = logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
    ])

try:
    env_path = f'{os.path.dirname(os.path.abspath(__file__))}/.env'
    logging.debug(f'Loading .env file from {env_path}')
    load_dotenv(env_path)
    KUMA_URL = os.environ['MON_UPTIME_KUMA_MEDIA_AVAILABLE_PUSH_URL']
    HMSD_APPS_PATH = os.environ['HMSD_APPS_PATH']

except KeyError as e:
    logging.error(f'Failed to find required environment variable: {e}')
    sys.exit(1)
except PermissionError as e:
    logging.error(f'You do not have permission to read the env file at: {env_path}')
    sys.exit(1)

def notify(status: str, message: str, ping: int = 0) -> int:
    """Sends a GET request to the Uptime Kuma host

    Args:
        ``status`` (``str``): The status of ``up`` or ``down``
        
        ``message`` (``str``): The message to send
        
        ``ping`` (``int``, optional): Value to send for 'ping'. Defaults to 0.

    Returns:
        ``int``: the HTTP status code
    """    
    logging.info(f'Sending notification:\n\tstatus: {status}\n\tmessage: {message}\n\tping: {ping}')
    push_notify = requests.get(f'{KUMA_URL}?status={status}&msg={message}&ping={ping}', verify=False)
    status_code = push_notify.status_code
    logging.debug(f'Sent notification, got status code: {status_code}')
    return status_code

def main():
    host = 'localhost:32400'
    
    logging.info(f'Checking Plex for media availability')
    logging.info(f'Pulling API key from Plex Preferences.xml file')
    with open(f'{HMSD_APPS_PATH}/plex/config/Library/Application Support/Plex Media Server/Preferences.xml', 'rb') as f:
        plex_config = xmltodict.parse(f)
    f.close()

    PLEX_TOKEN = plex_config['Preferences']['@PlexOnlineToken']
    session = requests.Session()
    session.headers.update({
        'X-Plex-Token': PLEX_TOKEN
    })
    session.verify = False    

    # Get available libraries
    url = f'https://{host}/library/sections'
    response = session.get(url)
    if response.status_code == 401:
        logging.error(f'Invalid Plex API key')
        notify('down', 'Plex API key invalid')
    data = xmltodict.parse(response.content)

    libarary_id = None
    # Get the first movie library found
    for libarary in data['MediaContainer']['Directory']:
        if libarary['@type'] == 'movie':
            libarary_id = libarary['@key']
            break

    if libarary_id is None:
        logging.error('No movie libraries found, exiting')
        sys.exit(1)

    # Get the newest movies
    url = f'{url}/{libarary_id}/newest'
    response = session.get(url)
    newest_movie_list = xmltodict.parse(response.content)

    # Get the first movies ID
    first_movie_id = newest_movie_list['MediaContainer']['Video'][0]['@ratingKey']

    # Get the first movies metadata
    url = f'https://{host}/library/metadata/{first_movie_id}?checkFiles=1'
    plex_response = session.get(url)
    ping = plex_response.elapsed.microseconds/1000

    # If not a 200, exit
    if plex_response.status_code != 200:
        notify('down', f'Plex unavailable (code: {plex_response.status_code})', ping)
        sys.exit(1)

    session.close()

    # Checking the metadata to see if it's available
    data = xmltodict.parse(plex_response.content)
    accessible = data['MediaContainer']['Video']['Media']['Part']['@accessible']
    exists = data['MediaContainer']['Video']['Media']['Part']['@exists']
    title = data['MediaContainer']['Video']['@title']

    logging.debug(f'checking: {title}')
    logging.debug(f'accessible value: {accessible}')
    logging.debug(f'exists value: {exists}')
    
    if accessible == '1' and exists == '1':
        notify('up', f'Media ({title}) is available', ping)
    elif accessible == '0' and exists == '0':
        notify('down', f'Media ({title}) unavailable', ping)
    else:
        notify('down', 'Unknown state', ping)


if __name__ == '__main__':
    main()
