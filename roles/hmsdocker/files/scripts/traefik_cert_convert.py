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
import defusedxml.ElementTree as ET
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
    PLEX_PUBLIC_HOSTNAME = os.getenv('PLEX_PUBLIC_HOSTNAME', 'plex')
    PLEX_CERT_PASSPHRASE = os.getenv('PLEX_CERTIFICATE_PASSPHRASE', None)
    PLEX_MODIFY_CONFIG = os.getenv('PLEX_CERT_UPDATE_CONFIG', False)
    PLEX_RESTART = os.getenv('PLEX_CERT_RESTART', False)
    # `traefik` or `caddy`, whichever reverse proxy gets the certificate
    CERT_SOURCE = os.getenv('PLEX_CERT_SOURCE', 'traefik')
except KeyError as e:
    logging.warning(f'Failed to find value for {e}')

PLEX_CONFIG_DIR = f"{HMSD_APPS_PATH}/plex/config"
TRAEFIK_CERT_DIR = f"{HMSD_APPS_PATH}/traefik/config/certs"
CADDY_CERT_DIR = f"{HMSD_APPS_PATH}/caddy/data/caddy/certificates"

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
    try:
        with open(filename, 'wb') as file:
            file.write(p12)
            logging.info(f'PKCS12 data written to {filename}{" and encrypted" if priv_passphrase is not None else ""}')
    except FileNotFoundError as e:
        logging.error(f'Failed to write PKCS12 file to {filename}, directory may not exist (Error: {e})')
        sys.exit(1)
    file.close()
    os.chmod(filename, 0o600)
    try:
        os.chown(filename, uid=int(HMSD_USER_ID), gid=int(HMSD_GROUP_ID))
    except PermissionError as e:
        logging.error(f'Failed to change ownership of file {filename}, try running script with sudo (Error: {e})')
        sys.exit(1)

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
        # deepcode ignore PT: Script allows user to input path to cert file
        json_data = json.load(open(path, 'r'))
    except FileNotFoundError as e:
        logging.error(f'Failed to find certificate file at {path}, has Traefik successfully created one? (Error: {e})')
        sys.exit(1)
    except PermissionError as e:
        logging.error(f'Permission denied, try running with sudo (Error: {e})')
        sys.exit(1)
    logging.debug(f'Successfully obtained Traefik certificate store data')
    return json_data

def get_traefik_certificates(path: str) -> list:
    """Gets the certificates from the Traefik certificate store

    Args:
        path (``str``): The path to the Traefik certificate file (default: acme.json)

    Returns:
        ``list``: One ``dict`` per certificate with the ``main`` domain, its ``sans``, and the PEM ``certificate`` and ``key``
    """
    traefik_json_data = get_traefik_cert_store(path)
    try:
        certificates = traefik_json_data['letsencrypt']['Certificates']
    except KeyError as e:
        logging.error(f'Failed to load Certificates from file ({path}), have certificates successfully provisioned yet? (Error: {e})')
        sys.exit(1)
    result = []
    for domain in certificates:
        domain_data = domain['domain']
        try:
            sans = domain_data['sans']
        except KeyError as e:
            logging.info(f'Did not find any SANs')
            sans = None
        logging.debug(f'Decoding Traefik certificate data')
        result.append({
            'main': domain_data['main'],
            'sans': sans,
            'key': base64.b64decode(domain['key']).decode().strip(),
            'certificate': base64.b64decode(domain['certificate']).decode().strip(),
        })
    return result

def get_caddy_certificates(path: str, hostname: str) -> list:
    """Gets the newest Caddy certificate that covers the hostname

    Caddy stores each certificate as ``<issuer>/<name>/<name>.crt`` and ``<name>.key`` in its data directory.
    Certificates from the production Let's Encrypt server are preferred over the staging server.

    Args:
        path (``str``): The path to the Caddy certificates directory
        hostname (``str``): The hostname the certificate must cover

    Returns:
        ``list``: The certificate in the same format as ``get_traefik_certificates``, or an empty list
    """
    candidates = []
    try:
        issuers = os.listdir(path)
    except FileNotFoundError as e:
        logging.error(f'Failed to find the Caddy certificates directory {path}, has Caddy successfully created a certificate? (Error: {e})')
        sys.exit(1)
    except PermissionError as e:
        logging.error(f'Permission denied, try running with sudo (Error: {e})')
        sys.exit(1)
    for issuer in issuers:
        issuer_dir = os.path.join(path, issuer)
        if not os.path.isdir(issuer_dir):
            continue
        for name in os.listdir(issuer_dir):
            cert_path = os.path.join(issuer_dir, name, f'{name}.crt')
            key_path = os.path.join(issuer_dir, name, f'{name}.key')
            if not (os.path.isfile(cert_path) and os.path.isfile(key_path)):
                continue
            with open(cert_path, 'r') as f:
                # Caddy stores the full chain, the first certificate is the leaf
                chain = f.read().strip()
            with open(key_path, 'r') as f:
                key = f.read().strip()
            leaf_pem = chain.split('-----END CERTIFICATE-----')[0] + '-----END CERTIFICATE-----'
            leaf = x509.load_pem_x509_certificate(str.encode(leaf_pem))
            try:
                names = leaf.extensions.get_extension_for_class(x509.SubjectAlternativeName).value.get_values_for_type(x509.DNSName)
            except x509.ExtensionNotFound:
                continue
            if not names:
                continue
            logging.debug(f'Found Caddy certificate {cert_path} for {names}')
            if not is_covered(hostname, names[0], names):
                continue
            candidates.append(({
                'main': names[0],
                'sans': names,
                'key': key,
                'certificate': leaf_pem,
            }, 'staging' not in issuer, leaf.not_valid_after_utc if hasattr(leaf, 'not_valid_after_utc') else leaf.not_valid_after))
    if not candidates:
        return []
    candidates.sort(key=lambda c: (c[1], c[2]), reverse=True)
    return [candidates[0][0]]

def is_covered(hostname: str, main_domain: str, sans: list) -> bool:
    """Checks if the hostname is covered by the certificate main domain or SANs

    Args:
        hostname (``str``): The hostname
        main_domain (``str``): The main domain of the certificate
        sans (``list``): The SANs of the certificate, or ``None``

    Returns:
        ``bool``: Whether the certificate covers the hostname
    """
    dns_parent_zone = '.'.join(hostname.split('.')[1:])
    if sans:
        for san in sans:
            logging.debug(f'\t\tFound SAN: {san}')
            if san.startswith('*.') and dns_parent_zone == san[2:]:
                logging.info(f'Hostname {hostname} is covered by SAN: {san}')
                return True
            if hostname == san:
                logging.info(f'Hostname {hostname} is covered by SAN: {san}')
                return True
    if hostname == main_domain:
        logging.info(f'Hostname {hostname} is covered by main domain: {main_domain}')
        return True
    return False

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
        description='Converts a Traefik or Caddy certificate to PKCS12 format and applies it to a Plex server'
    )
    parser.add_argument('-r', '--restart-plex', choices=[True, False], default=PLEX_RESTART, help='Whether or not to restart the Plex container when updating the server config')
    parser.add_argument('-s', '--hostname', default=PLEX_PUBLIC_HOSTNAME, help='The publicly accessible hostname to access the Plex server. Must be in scope of the certificate domain or a SAN')
    parser.add_argument('-p', '--passphrase', default=PLEX_CERT_PASSPHRASE, help='Passphrase to protect the PKSC12 certificate file')
    parser.add_argument('-c', '--plex-config', default=f'{PLEX_CONFIG_DIR}/Library/Application Support/Plex Media Server/Preferences.xml', help='Path to the Plex servers Preferences.xml file')
    parser.add_argument('-m', '--modify-plex-config', choices=[True, False], default=PLEX_MODIFY_CONFIG, help='If True, this will update the Plex config file to point to the converted certificate file')
    parser.add_argument('-t', '--traefik-cert-file', default=f'{TRAEFIK_CERT_DIR}/acme.json', help='Path to Traefik certificate file')
    parser.add_argument('--caddy-cert-dir', default=CADDY_CERT_DIR, help='Path to the Caddy certificates directory')
    parser.add_argument('--cert-source', choices=['traefik', 'caddy'], default=CERT_SOURCE, help='The reverse proxy that gets the certificate')
    parser.add_argument('-n', '--compose-project', default=COMPOSE_PROJECT, help='Name of the Docker Compose project where the target containers are running')
    args = parser.parse_args()
    restart = args.restart_plex
    compose_project = args.compose_project
    passphrase = args.passphrase
    traefik_cert_file_path = args.traefik_cert_file
    plex_config_path = args.plex_config
    plex_hostname = args.hostname
    modify_plex_conf = args.modify_plex_config

    if passphrase == "":
        passphrase = None

    existing_certificate_dir = PLEX_CONFIG_DIR
    
    if args.cert_source == 'caddy':
        logging.info(f'Using Caddy certificates directory: {args.caddy_cert_dir}')
        certificates = get_caddy_certificates(args.caddy_cert_dir, plex_hostname)
        if not certificates:
            logging.error(f'Hostname {plex_hostname} is NOT covered by any Caddy certificate, cannot continue')
            sys.exit(1)
    else:
        logging.info(f'Using Traefik certificate file: {traefik_cert_file_path}')
        certificates = get_traefik_certificates(traefik_cert_file_path)

    for domain in certificates:
        main_domain = domain['main']
        sans = domain['sans']
        certificate_priv_key = domain['key']
        certificate = domain['certificate']
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
        logging.debug(f'Checking if hostname {plex_hostname} is covered by main domain or SANs')
        if not is_covered(plex_hostname, main_domain, sans):
            logging.error(f'Hostname {plex_hostname} is NOT covered by main domain or SANs, cannot continue')
            sys.exit(1)

        logging.debug(f'Getting serial for {args.cert_source} certificate')
        new_serial = get_pem_serial(certificate)

        logging.debug(f'Comparing: {current_serial} to {new_serial}')
        if current_serial != new_serial:
            logging.info(f'Serials DO NOT match, updating file')
            convert_to_pkcs12(pkcs12_file_path, certificate, certificate_priv_key, priv_passphrase=passphrase)
            if modify_plex_conf:
                modify_plex_config(plex_config_path, 'customCertificateDomain', f'{plex_hostname}')
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
