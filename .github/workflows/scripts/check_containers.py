#!/usr/bin/env python3

import sys
import docker
import os
import logging
import requests
from dotenv import load_dotenv

# Intended as the containers may host a self-signed certificate
import urllib3
urllib3.disable_warnings()

LOG_PATH = f"{os.path.dirname(os.path.abspath(__file__))}/backups.log"
logger = logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_PATH, mode='a'),
        logging.StreamHandler(),
    ])

logging.info(f'Initializing Docker client')
docker_client = docker.from_env()

def main():
    container_list = docker_client.containers.list()

    project = 'hms-docker'

    requests_made = 0
    success_codes = 0
    failure_codes = 0
    
    for cont in container_list:
        try:
            name = cont.name
            logging.debug(f'Checking {name}')
            if cont.labels['com.docker.compose.project'] == project:
                workdir = cont.labels['com.docker.compose.project.working_dir']
                load_dotenv(f'{workdir}/.env')
                domain = os.getenv('HMSD_DOMAIN')
                for port_exposures in cont.attrs['NetworkSettings']['Ports']:
                    port_map = cont.attrs['NetworkSettings']['Ports'][port_exposures]
                    if port_map is None or 'udp' in port_exposures:
                        continue
                    logging.debug(f'{name} is in project {project} and has tcp port exposure: {port_exposures}')
                    for mapping in port_map:
                        host_ip = mapping['HostIp']
                        host_port  = mapping['HostPort']
                        if host_ip == '::':
                            continue
                        if host_ip == '0.0.0.0':
                            host_ip = '127.0.0.1'

                        try:
                            suffix = ''
                            ssl = False
                            if name == 'plex':
                                suffix = '/web'
                                ssl = True
                                if host_port != '32400':
                                    logging.debug(f'Skipping {name} on {host_port} because it doesnt host a webpage')
                                    continue
                            if name == 'transmission' and host_port == '8888':
                                logging.debug(f'Skipping {name} on {host_port} because its a proxy')
                                continue
                            if name == 'authentik-server':
                                name = 'authentik'
                                ssl = True
                            url = f'http{"s" if ssl else ""}://{host_ip}:{host_port}{suffix}'
                            host_header = f'{name}.{domain}'
                            logging.debug(f'getting {url} with Host header {host_header}')
                            # file deepcode ignore SSLVerificationBypass: Containers may host a self-signed certificate
                            response = requests.get(url, verify=False, headers={
                                'Host': host_header
                            })
                            requests_made += 1
                            status_code = response.status_code
                            if status_code == 200:
                                success_codes += 1
                                logging.info(f'{name}:{host_port} OK')
                            elif name == 'transmission-proxy' and status_code == '502':
                                success_codes += 1
                            else:
                                failure_codes += 1
                                logging.warning(f'{name}:{host_port} FAILED (Code: {status_code})')
                        except requests.exceptions.ConnectionError as e:
                            logging.error(f'Failed on port {host_port} with header {host_header}: {e}')

        except KeyError as e:
            logging.debug(f'{name} is not in the project {project}')
            continue
    if requests_made > 0:
        fail_rate = failure_codes/requests_made
    else:
        logging.error(f'Did not make any requests, exiting')
        sys.exit(1)
    threshold = 0.34
    if fail_rate > threshold:
        logging.error(f'Failure rate exceeded {threshold}, it was {fail_rate}')
        sys.exit(1)
    else:
        logging.info(f'Failure rate: {fail_rate}')
        sys.exit(0)

if __name__ == '__main__':
    main()
