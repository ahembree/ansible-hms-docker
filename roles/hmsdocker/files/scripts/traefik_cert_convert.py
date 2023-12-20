#!/usr/bin/env python
import logging
import os
from datetime import datetime

LOG_PATH=f"{os.path.dirname(os.path.abspath(__file__))}/cert_convert.log"
logger = logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_PATH, mode='a'),
        logging.StreamHandler(),
    ])
start_time = datetime.now()
logging.info(f'{"=" * 15} Starting Script at {start_time} {"=" * 15}')

import json
import base64
from cryptography import x509
from cryptography.hazmat.primitives.serialization import BestAvailableEncryption, NoEncryption, load_pem_private_key, pkcs12
import sys
import xml.etree.ElementTree as ET
import argparse
import docker
from dotenv import load_dotenv

docker_client = docker.from_env()

try:
    load_dotenv(f'{os.path.dirname(os.path.abspath(__file__))}/.env')
    HMSD_APPS_PATH = os.getenv('HMSD_APPS_PATH', '/opt/hms-docker/apps')
    COMPOSE_PROJECT = os.getenv('COMPOSE_PROJECT', 'hms-docker')
    HMSD_USER_ID = os.getenv('PUID', 1234)
    HMSD_GROUP_ID = os.getenv('PGID', 1234)
    PLEX_PUBLIC_SUBDOMAIN = os.getenv('PLEX_PUBLIC_SUBDOMAIN', 'plex')
    PLEX_CERT_PASSPHRASE = os.getenv('PLEX_CERTIFICATE_PASSPHRASE', None)
    PLEX_MODIFY_CONFIG = os.getenv('PLEX_CERT_UPDATE_CONFIG', False)
    PLEX_RESTART = os.getenv('PLEX_CERT_RESTART', False)
except KeyError as e:
    logging.warning(f'Failed to find value for {e}')

PLEX_CONFIG_DIR = f"{HMSD_APPS_PATH}/plex/config"
TRAEFIK_CERT_DIR = f"{HMSD_APPS_PATH}/traefik/config/certs"

def convert_to_pkcs12(filename: str, pub: str, priv: str, priv_passphrase: str=None) -> None:
    """Converts PEM data into PKCS12 format and outputs to a file

    Args:
        filename (``str``): The path to the output file
        pub (``str``): The public certificate data
        priv (``str``): The certificate private key data
        priv_passphrase (``str``, optional): The private key passphrase. Defaults to ``None``.
    """    
    logging.debug(f'Converting to PKCS12 and outputting file to {filename}')
    cert = x509.load_pem_x509_certificate(str.encode(pub))
    if priv_passphrase is not None:
        key = load_pem_private_key(str.encode(priv), str.encode(priv_passphrase))
        p12 = pkcs12.serialize_key_and_certificates(None, key, cert, None, BestAvailableEncryption(str.encode(priv_passphrase)))
    else:
        key = load_pem_private_key(str.encode(priv), None)
        p12 = pkcs12.serialize_key_and_certificates(None, key, cert, None, NoEncryption())
    with open(filename, 'wb') as file:
        file.write(p12)
        logging.info(f'PKCS12 data written to {filename}{" and encrypted" if priv_passphrase is not None else ""}')
    file.close()
    os.chmod(filename, 0o600)
    os.chown(filename, uid=int(HMSD_USER_ID), gid=int(HMSD_GROUP_ID))

def modify_plex_config(config_path: str, attrib_key: str, attrib_value: str) -> None:
    """Modifies the Plex server config XML file to have expected values output by this script

    Args:
        config_path (``str``): The path to the Plex "Preferences.xml" file
        attrib_key (``str``): The attribute key to update
        attrib_value (``str``): The value to assign to the attribute key
    """    
    try:
        logging.debug(f'Trying to load Plex config from {config_path}')
        xml_tree = ET.parse(config_path)
    except FileNotFoundError as e:
        logging.error(f'Failed to find config file at location: {config_path} for reason: {e}')
        sys.exit(1)
    except PermissionError as e:
        logging.error(f'Failed to read config file, permission denied, try running as root? {e}')
        sys.exit(1)

    xml_root = xml_tree.getroot()
    try:
        if xml_root.attrib[attrib_key] != attrib_value:
            logging.info(f'Updating Plex preference: {attrib_key}')
            xml_root.attrib[attrib_key] = attrib_value
            logging.debug(f'Writing XML tree to file')
            xml_tree.write(config_path)
        else:
            logging.debug(f'{attrib_key} already equals expected value')
    except KeyError as e:
        logging.info(f'Did not find key {attrib_key}, creating and setting value')
        xml_root.attrib[attrib_key] = attrib_value
        logging.debug(f'Writing XML tree to file')
        xml_tree.write(config_path)
    

def get_pkcs12_serial(data: bytes, passph: str=None) -> str:
    """Gets the serial from a PKCS12 file

    Args:
        data (``bytes``): The certificate file binary data
        passph (``str``, optional): The files passphrase. Defaults to ``None``.

    Returns:
        ``str``: The serial of the PKCS12 file
    """    
    logging.debug('Obtaining PKCS12 certificate serial number')
    serial = pkcs12.load_pkcs12(data, passph).cert.certificate.serial_number
    logging.debug(f'PKSC12 Serial: {serial}')
    return serial

def get_pem_serial(certificate: str, private: bool=False, passphrase: str=None) -> str:
    """Gets the serial from PEM data

    Args:
        certificate (``str``): The certificate data in PEM format
        private (``bool``, optional): Whether it's a private key or not. Defaults to ``False``.
        passphrase (``bool``, optional): The private keys passphrase. Defaults to ``None``.

    Returns:
        ``str``: The serial of the PEM data
    """    
    logging.debug(f'Obtaining PEM certificate serial number')
    serial = x509.load_pem_x509_certificate(str.encode(certificate)).serial_number
    logging.debug(f'PEM Serial: {serial}')
    return serial

def get_traefik_cert_store(path: str) -> dict:
    """Gets the Traefik certificate store data

    Args:
        ``path`` (``str``): The path to the Traefik certificate file (default: acme.json)

    Returns:
        ``dict``: The Traefik certificate file in JSON/dict format
    """    
    try:
        logging.debug(f'Attempting to load Traefik certificate store file')
        json_data = json.load(open(path, 'r'))
    except FileNotFoundError as e:
        logging.error(f'Failed to find certificate file at {path}, has Traefik successfully created one? (Error: {e})')
        sys.exit(1)
    except PermissionError as e:
        logging.error(f'Permission denied, try running with sudo (Error: {e})')
        sys.exit(1)
    logging.debug(f'Successfully obtained Traefik certificate store data')
    return json_data

def restart_plex(compose_project: str) -> None:
    """Restarts the Plex container in the defined Compose project

    Args:
        compose_project (``str``): The Compose project where the Plex container is
    """    
    container = get_container_by_image('lscr.io/linuxserver/plex')
    if container is type(list):
        for con in container:
            if con.labels['com.docker.compose.project'] == compose_project:
                logging.warning(f'Restarting container ID: {con.short_id}')
                con.restart()
    else:
        if container.labels['com.docker.compose.project'] == compose_project:
            logging.warning(f'Restarting container ID: {container.short_id}')
            container.restart()

def get_container_by_image(image: str):
    """Gets the Container object based on the image name

    Args:
        image (``str``): The image used to start the container

    Returns:
        ``str`` or ``list``: The Container object or list of Container objects
    """    
    container_list = docker_client.containers.list(filters={
        'ancestor': image
    })
    if len(container_list) == 1:
        return container_list[0]
    else:
        logging.warning(f'Got more than one container for image {image}, found: {len(container_list)}')
        return container_list

def main():
    parser = argparse.ArgumentParser(
        prog='traefik-to-plex-pkcs12',
        description='Converts a Traefik certificate file to PKCS12 format and applies it to a Plex server'
    )
    parser.add_argument('-r', '--restart-plex', choices=[True, False], default=PLEX_RESTART, help='Whether or not to restart the Plex container when updating the server config')
    parser.add_argument('-s', '--subdomain', default=PLEX_PUBLIC_SUBDOMAIN, help='The publicly accessible subdomain to access the Plex server. Must be in scope of the main certificate domain or a SAN')
    parser.add_argument('-p', '--passphrase', default=PLEX_CERT_PASSPHRASE, help='Passphrase to protect the PKSC12 certificate file')
    parser.add_argument('-c', '--plex-config', default=f'{PLEX_CONFIG_DIR}/Library/Application Support/Plex Media Server/Preferences.xml', help='Path to the Plex servers Preferences.xml file')
    parser.add_argument('-m', '--modify-plex-config', choices=[True, False], default=PLEX_MODIFY_CONFIG, help='If True, this will update the Plex config file to point to the converted certificate file')
    parser.add_argument('-t', '--traefik-cert-file', default=f'{TRAEFIK_CERT_DIR}/acme.json', help='Path to Traefik certificate file')
    parser.add_argument('-n', '--compose-project', default=COMPOSE_PROJECT, help='Name of the Docker Compose project where the target containers are running')
    args = parser.parse_args()
    restart = args.restart_plex
    compose_project = args.compose_project
    passphrase = args.passphrase
    traefik_cert_file_path = args.traefik_cert_file
    plex_config_path = args.plex_config
    plex_subdomain = args.subdomain
    modify_plex_conf = args.modify_plex_config

    if passphrase == "":
        passphrase = None

    existing_certificate_dir = PLEX_CONFIG_DIR
    
    logging.info(f'Using Traefik certificate file: {traefik_cert_file_path}')

    traefik_json_data = get_traefik_cert_store(traefik_cert_file_path)
    try:
        certificates = traefik_json_data['letsencrypt']['Certificates']
    except KeyError as e:
        logging.error(f'Failed to load Certificates from file ({traefik_cert_file_path}), have certificates successfully provisioned yet? (Error: {e})')
        sys.exit(1)
    for domain in certificates:
        domain_data = domain['domain']
        main_domain = domain_data['main']
        try:
            sans = domain_data['sans']
        except KeyError as e:
            logging.info(f'Did not find any SANs')
            sans = None
        logging.debug(f'Decoding Traefik certificate data')
        certificate_priv_key = base64.b64decode(domain['key']).decode().strip()
        certificate = base64.b64decode(domain['certificate']).decode().strip()
        pkcs12_file_name = f'{"".join(character for character in main_domain if character.isalnum())}.pfx'
        pkcs12_file_path = f'{existing_certificate_dir}{"/" if not existing_certificate_dir.endswith("/") else ""}{pkcs12_file_name}'

        current_serial = None
        if os.path.exists(pkcs12_file_path):
            logging.info(f'Found existing PKCS12 file in path: {pkcs12_file_path}')
            logging.debug(f'Getting the existing PKCS12 file serial')
            with open(pkcs12_file_path, 'rb') as f:
                current_serial = get_pkcs12_serial(f.read())
            f.close()

        logging.debug(f'Working with main domain: {main_domain}')
        if sans:
            for san in sans:
                logging.debug(f'\t\tFound SAN: {san}')

        logging.debug(f'Getting serial for Traefik certificate')
        new_serial = get_pem_serial(certificate)

        logging.debug(f'Comparing: {current_serial} to {new_serial}')
        if current_serial != new_serial:
            logging.info(f'Serials DO NOT match, updating file')
            convert_to_pkcs12(pkcs12_file_path, certificate, certificate_priv_key, priv_passphrase=passphrase)
            if modify_plex_conf:
                modify_plex_config(plex_config_path, 'customCertificateDomain', f'{plex_subdomain}.{main_domain}')
                modify_plex_config(plex_config_path, 'customCertificatePath', f'/config/{pkcs12_file_name}')
                if passphrase:
                    modify_plex_config(plex_config_path, 'customCertificateKey', passphrase)
                if restart:
                    logging.warning(f'Restarting plex in project: {compose_project}')
                    restart_plex(compose_project)
        else:
            logging.info(f'Certificate serials MATCH, doing nothing')
            break

    stop_time = datetime.now()
    logging.info(f'{"=" * 15} Finished at {stop_time}, took {stop_time - start_time} {"=" * 15}')

if __name__ == '__main__':
    main()
