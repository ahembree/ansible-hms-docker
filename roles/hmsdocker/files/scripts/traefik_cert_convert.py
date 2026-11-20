#!/usr/bin/env python
"""Converts a Traefik (ACME) certificate to PKCS12 and applies it to a Plex server.

Traefik stores each certificate in acme.json as a PEM bundle (leaf + intermediates)
alongside its private key. Plex wants a single PKCS12 file, which must contain the
intermediates as well or clients that validate strictly will reject the connection.
"""
import argparse
import base64
import io
import json
import logging
import os
import re
import stat
import sys
import tempfile
from datetime import datetime
from logging.handlers import RotatingFileHandler
from typing import Dict, List, Optional, Tuple

import defusedxml.ElementTree as ET
from cryptography import x509
from cryptography.hazmat.primitives.serialization import (
    BestAvailableEncryption,
    Encoding,
    NoEncryption,
    PublicFormat,
    load_pem_private_key,
    pkcs12,
)
from dotenv import load_dotenv

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_PATH = f"{SCRIPT_DIR}/cert_convert.log"
PEM_CERT_RE = re.compile(rb'-----BEGIN CERTIFICATE-----.+?-----END CERTIFICATE-----', re.DOTALL)
TRUE_VALUES = {'1', 'true', 'yes', 'y', 'on'}
FALSE_VALUES = {'', '0', 'false', 'no', 'n', 'off', 'none', 'null'}
PLEX_COMPOSE_SERVICE = 'plex'
PLEX_STOP_TIMEOUT = 60


def str_to_bool(value) -> bool:
    """Parses a boolean from a CLI argument or environment variable

    Environment variables and CLI arguments are always strings, so ``"False"`` must not be
    treated as truthy.

    Args:
        value: The value to parse

    Returns:
        ``bool``: The parsed value
    """
    if isinstance(value, bool):
        return value
    normalized = str(value).strip().lower()
    if normalized in TRUE_VALUES:
        return True
    if normalized in FALSE_VALUES:
        return False
    raise argparse.ArgumentTypeError(f'Expected a boolean (true/false), got: {value!r}')


def env_bool(name: str, default: bool = False) -> bool:
    """Reads a boolean from an environment variable

    Args:
        name (``str``): The environment variable name
        default (``bool``, optional): Value to use when the variable is unset. Defaults to ``False``.

    Returns:
        ``bool``: The parsed value
    """
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return str_to_bool(value)
    except argparse.ArgumentTypeError as e:
        sys.exit(f'Invalid value for {name}: {e}')


def setup_logging(verbose: bool = False) -> None:
    """Configures logging to the console and a size-capped log file next to the script

    Args:
        verbose (``bool``, optional): Enables debug logging. Defaults to ``False``.
    """
    handlers: List[logging.Handler] = [logging.StreamHandler()]
    file_error = None
    try:
        handlers.append(RotatingFileHandler(LOG_PATH, maxBytes=1_000_000, backupCount=3))
    except OSError as e:
        file_error = e
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s [%(name)s] [%(levelname)s] %(message)s",
        handlers=handlers)
    if file_error:
        logging.warning(f'Could not open log file {LOG_PATH}, logging to console only (Error: {file_error})')


def atomic_write(path: str, data: bytes, mode: int, uid: Optional[int] = None, gid: Optional[int] = None) -> None:
    """Writes a file so that readers only ever see the old or the new contents

    The data is written to a temporary file (created with mode 0600) in the same directory,
    permissions and ownership are applied, and it is then renamed over the destination.

    Args:
        path (``str``): The destination path
        data (``bytes``): The data to write
        mode (``int``): The file mode to apply
        uid (``int``, optional): The owning user ID. Defaults to ``None`` (unchanged).
        gid (``int``, optional): The owning group ID. Defaults to ``None`` (unchanged).
    """
    directory = os.path.dirname(path) or '.'
    fd, tmp_path = tempfile.mkstemp(dir=directory, prefix=f'.{os.path.basename(path)}.')
    try:
        with os.fdopen(fd, 'wb') as file:
            file.write(data)
            file.flush()
            os.fsync(file.fileno())
        os.chmod(tmp_path, mode)
        if uid is not None and gid is not None:
            os.chown(tmp_path, uid, gid)
        os.replace(tmp_path, path)
    except BaseException:
        try:
            os.unlink(tmp_path)
        except FileNotFoundError:
            pass
        raise


def spki(public_key) -> bytes:
    """Returns the DER encoded SubjectPublicKeyInfo of a public key, used to compare keys"""
    return public_key.public_bytes(Encoding.DER, PublicFormat.SubjectPublicKeyInfo)


def load_cert_bundle(pem: bytes) -> List[x509.Certificate]:
    """Loads every certificate found in PEM data

    Args:
        pem (``bytes``): One or more concatenated PEM certificates

    Returns:
        ``list``: The certificates in the order they appear
    """
    certs = [x509.load_pem_x509_certificate(block) for block in PEM_CERT_RE.findall(pem)]
    if not certs:
        raise ValueError('No certificates found in PEM data')
    return certs


def split_leaf_and_chain(certs: List[x509.Certificate], key) -> Tuple[x509.Certificate, List[x509.Certificate]]:
    """Separates the certificate that belongs to the private key from the rest of the chain

    Args:
        certs (``list``): All certificates from the bundle
        key: The private key

    Returns:
        ``tuple``: The leaf certificate and the list of remaining (intermediate) certificates
    """
    key_spki = spki(key.public_key())
    for index, cert in enumerate(certs):
        if spki(cert.public_key()) == key_spki:
            return cert, certs[:index] + certs[index + 1:]
    raise ValueError('None of the certificates match the private key')


def cert_expiry(cert: x509.Certificate) -> datetime:
    """Returns the expiry of a certificate as a naive UTC datetime, on old and new cryptography versions"""
    expiry = getattr(cert, 'not_valid_after_utc', None)
    if expiry is None:
        return cert.not_valid_after
    return expiry.replace(tzinfo=None)


def build_pkcs12(key, leaf: x509.Certificate, chain: List[x509.Certificate], passphrase: Optional[str] = None) -> bytes:
    """Serializes a key, its certificate and the intermediate chain to PKCS12

    Args:
        key: The private key
        leaf (``x509.Certificate``): The certificate matching the private key
        chain (``list``): The intermediate certificates
        passphrase (``str``, optional): Passphrase to encrypt the file with. Defaults to ``None``.

    Returns:
        ``bytes``: The PKCS12 data
    """
    encryption = BestAvailableEncryption(passphrase.encode()) if passphrase else NoEncryption()
    return pkcs12.serialize_key_and_certificates(None, key, leaf, chain or None, encryption)


def pkcs12_is_current(path: str, passphrase: Optional[str], leaf: x509.Certificate, chain: List[x509.Certificate]) -> bool:
    """Checks whether an existing PKCS12 file already holds the expected certificate, chain and encryption

    Args:
        path (``str``): The path to the existing PKCS12 file
        passphrase (``str``, optional): The passphrase the file is expected to be encrypted with
        leaf (``x509.Certificate``): The expected certificate
        chain (``list``): The expected intermediate certificates

    Returns:
        ``bool``: ``True`` if the file does not need to be regenerated
    """
    try:
        with open(path, 'rb') as file:
            data = file.read()
    except FileNotFoundError:
        logging.info(f'No existing PKCS12 file at {path}')
        return False
    logging.info(f'Found existing PKCS12 file in path: {path}')

    try:
        existing = pkcs12.load_pkcs12(data, None)
        encrypted = False
    except ValueError:
        existing = None
        encrypted = True

    if encrypted != bool(passphrase):
        logging.info(f'Existing PKCS12 file is {"encrypted" if encrypted else "not encrypted"} but a passphrase is {"set" if passphrase else "not set"}')
        return False
    if encrypted:
        try:
            existing = pkcs12.load_pkcs12(data, passphrase.encode())
        except ValueError:
            logging.warning('Existing PKCS12 file could not be read with the configured passphrase')
            return False

    if existing.cert is None or existing.cert.certificate != leaf:
        logging.info('Existing PKCS12 file holds a different certificate')
        return False
    if [extra.certificate for extra in existing.additional_certs] != chain:
        logging.info('Existing PKCS12 file holds a different (or no) intermediate chain')
        return False
    return True


def covering_name(hostname: str, names: List[str]) -> Optional[str]:
    """Finds the certificate name that covers a hostname

    A name covers the hostname if it is an exact match, or if it is a wildcard for the
    hostname's parent zone (a wildcard only ever matches a single label).

    Args:
        hostname (``str``): The hostname to check
        names (``list``): The certificate's main domain and SANs

    Returns:
        ``str``: The name that covers the hostname, or ``None``
    """
    hostname = hostname.strip().lower().rstrip('.')
    parent_zone = hostname.split('.', 1)[1] if '.' in hostname else None
    for name in names:
        normalized = name.strip().lower().rstrip('.')
        if normalized == hostname:
            return name
        if normalized.startswith('*.') and parent_zone and normalized[2:] == parent_zone:
            return name
    return None


def get_traefik_cert_store(path: str) -> dict:
    """Gets the Traefik certificate store data

    Args:
        ``path`` (``str``): The path to the Traefik certificate file (default: acme.json)

    Returns:
        ``dict``: The Traefik certificate file in JSON/dict format
    """
    try:
        logging.debug('Attempting to load Traefik certificate store file')
        # deepcode ignore PT: Script allows user to input path to cert file
        with open(path, 'r') as file:
            json_data = json.load(file)
    except FileNotFoundError as e:
        logging.error(f'Failed to find certificate file at {path}, has Traefik successfully created one? (Error: {e})')
        sys.exit(1)
    except PermissionError as e:
        logging.error(f'Permission denied, try running with sudo (Error: {e})')
        sys.exit(1)
    except json.JSONDecodeError as e:
        logging.error(f'Certificate file at {path} is empty or not valid JSON, have certificates successfully provisioned yet? (Error: {e})')
        sys.exit(1)
    logging.debug('Successfully obtained Traefik certificate store data')
    return json_data


def select_certificate(entries: list, hostname: str) -> Optional[dict]:
    """Picks the certificate that covers the hostname, preferring the one that expires last

    Args:
        entries (``list``): The certificate entries of a Traefik certificate resolver
        hostname (``str``): The hostname the certificate must cover

    Returns:
        ``dict``: The selected certificate (main domain, key, leaf, chain), or ``None`` if nothing covers the hostname
    """
    selected = None
    for entry in entries:
        domain_data = entry.get('domain') or {}
        main_domain = domain_data.get('main')
        if not main_domain:
            continue
        names = [main_domain] + (domain_data.get('sans') or [])
        covered_by = covering_name(hostname, names)
        if covered_by is None:
            logging.debug(f'Certificate for {main_domain} does not cover {hostname}, skipping')
            continue
        logging.debug(f'Hostname {hostname} is covered by {covered_by} (certificate main domain: {main_domain})')
        try:
            key = load_pem_private_key(base64.b64decode(entry['key']), None)
            leaf, chain = split_leaf_and_chain(load_cert_bundle(base64.b64decode(entry['certificate'])), key)
        except (KeyError, ValueError, TypeError) as e:
            logging.warning(f'Skipping unusable certificate for {main_domain} (Error: {e})')
            continue
        candidate = {'main_domain': main_domain, 'covered_by': covered_by, 'key': key, 'leaf': leaf, 'chain': chain}
        if selected is None or cert_expiry(leaf) > cert_expiry(selected['leaf']):
            selected = candidate
    if selected is not None:
        logging.info(f'Hostname {hostname} is covered by {selected["covered_by"]} (certificate main domain: {selected["main_domain"]}, expires: {cert_expiry(selected["leaf"])} UTC)')
    return selected


def sync_plex_config(config_path: str, desired: Dict[str, str], dry_run: bool = False) -> List[str]:
    """Ensures the Plex server config XML file has the expected attribute values

    Args:
        config_path (``str``): The path to the Plex "Preferences.xml" file
        desired (``dict``): The attribute keys and the values they should have
        dry_run (``bool``, optional): Only report what would change. Defaults to ``False``.

    Returns:
        ``list``: The attribute keys that differ (dry run) or were updated
    """
    try:
        logging.debug(f'Trying to load Plex config from {config_path}')
        xml_tree = ET.parse(config_path)
        config_stat = os.stat(config_path)
    except FileNotFoundError as e:
        logging.error(f'Failed to find config file at location: {config_path} for reason: {e}')
        sys.exit(1)
    except PermissionError as e:
        logging.error(f'Failed to read config file, permission denied, try running as root? {e}')
        sys.exit(1)
    except ET.ParseError as e:
        logging.error(f'Failed to parse config file at location: {config_path} for reason: {e}')
        sys.exit(1)

    xml_root = xml_tree.getroot()
    # A missing attribute is equivalent to an empty value
    changed = [key for key, value in desired.items() if xml_root.attrib.get(key, '') != value]
    if not changed:
        logging.debug('Plex config already has the expected values')
        return changed
    if dry_run:
        return changed

    for key in changed:
        logging.info(f'Updating Plex preference: {key}')
        xml_root.attrib[key] = desired[key]
    buffer = io.BytesIO()
    xml_tree.write(buffer, encoding='utf-8', xml_declaration=True)
    try:
        atomic_write(config_path, buffer.getvalue(), stat.S_IMODE(config_stat.st_mode), config_stat.st_uid, config_stat.st_gid)
    except PermissionError as e:
        logging.error(f'Failed to write config file, permission denied, try running as root? {e}')
        sys.exit(1)
    return changed


def get_plex_container(compose_project: str):
    """Gets the running Plex container of the defined Compose project

    Args:
        compose_project (``str``): The Compose project where the Plex container is

    Returns:
        The Container object, or ``None`` if there is not exactly one running Plex container
    """
    # Imported here so the Docker SDK and socket are only needed when a restart is requested
    import docker
    try:
        container_list = docker.from_env().containers.list(filters={
            'label': [
                f'com.docker.compose.project={compose_project}',
                f'com.docker.compose.service={PLEX_COMPOSE_SERVICE}',
            ]
        })
    except docker.errors.DockerException as e:
        logging.error(f'Failed to query Docker for the Plex container (Error: {e})')
        return None
    if len(container_list) != 1:
        logging.warning(f'Expected exactly one running "{PLEX_COMPOSE_SERVICE}" container in project {compose_project}, found: {len(container_list)}')
        return None
    return container_list[0]


def parse_args() -> argparse.Namespace:
    """Parses CLI arguments, with defaults coming from the environment / .env file"""
    apps_path = os.getenv('HMSD_APPS_PATH', '/opt/hms-docker/apps')
    plex_config_dir = f'{apps_path}/plex/config'
    parser = argparse.ArgumentParser(
        prog='traefik-to-plex-pkcs12',
        description='Converts a Traefik certificate file to PKCS12 format and applies it to a Plex server'
    )
    parser.add_argument('-r', '--restart-plex', type=str_to_bool, nargs='?', const=True, default=env_bool('PLEX_CERT_RESTART'), metavar='BOOL', help='Whether or not to restart the Plex container when the certificate or server config changed')
    parser.add_argument('-s', '--hostname', default=os.getenv('PLEX_PUBLIC_HOSTNAME', 'plex'), help='The publicly accessible hostname to access the Plex server. Must be in scope of the certificate domain or a SAN')
    parser.add_argument('-p', '--passphrase', default=os.getenv('PLEX_CERTIFICATE_PASSPHRASE'), help='Passphrase to protect the PKCS12 certificate file')
    parser.add_argument('-c', '--plex-config', default=f'{plex_config_dir}/Library/Application Support/Plex Media Server/Preferences.xml', help='Path to the Plex servers Preferences.xml file')
    parser.add_argument('-m', '--modify-plex-config', type=str_to_bool, nargs='?', const=True, default=env_bool('PLEX_CERT_UPDATE_CONFIG'), metavar='BOOL', help='If true, this will update the Plex config file to point to the converted certificate file')
    parser.add_argument('-t', '--traefik-cert-file', default=f'{apps_path}/traefik/config/certs/acme.json', help='Path to Traefik certificate file')
    parser.add_argument('-n', '--compose-project', default=os.getenv('COMPOSE_PROJECT', 'hms-docker'), help='Name of the Docker Compose project where the target containers are running')
    parser.add_argument('-o', '--output-dir', default=plex_config_dir, help='Directory to write the PKCS12 file to. Must be the directory mounted to /config in the Plex container')
    parser.add_argument('--resolver', default='letsencrypt', help='Name of the Traefik certificate resolver to read certificates from')
    parser.add_argument('-f', '--force', action='store_true', help='Regenerate the PKCS12 file even if it is already up to date')
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable debug logging')
    return parser.parse_args()


def main():
    load_dotenv(f'{SCRIPT_DIR}/.env')
    args = parse_args()
    setup_logging(args.verbose)
    start_time = datetime.now()
    logging.info(f'{"=" * 15} Starting Script at {start_time} {"=" * 15}')

    passphrase = args.passphrase or None
    plex_hostname = args.hostname
    try:
        uid = int(os.getenv('PUID', 1234))
        gid = int(os.getenv('PGID', 1234))
    except ValueError as e:
        logging.error(f'PUID and PGID must be numeric (Error: {e})')
        sys.exit(1)

    logging.info(f'Using Traefik certificate file: {args.traefik_cert_file}')
    traefik_json_data = get_traefik_cert_store(args.traefik_cert_file)
    try:
        certificates = traefik_json_data[args.resolver]['Certificates'] or []
    except (KeyError, TypeError) as e:
        logging.error(f'Failed to load Certificates for resolver "{args.resolver}" from file ({args.traefik_cert_file}), have certificates successfully provisioned yet? (Error: {e})')
        sys.exit(1)

    selected = select_certificate(certificates, plex_hostname)
    if selected is None:
        logging.error(f'Hostname {plex_hostname} is NOT covered by the main domain or SANs of any usable certificate, cannot continue')
        sys.exit(1)
    leaf, chain = selected['leaf'], selected['chain']
    if not chain:
        logging.warning('Traefik certificate has no intermediate certificates, clients may fail to validate it')

    pkcs12_file_name = f'{"".join(character for character in selected["main_domain"] if character.isalnum())}.pfx'
    pkcs12_file_path = os.path.join(args.output_dir, pkcs12_file_name)

    cert_changed = args.force or not pkcs12_is_current(pkcs12_file_path, passphrase, leaf, chain)
    if cert_changed:
        logging.info(f'Writing certificate (serial {leaf.serial_number}) and {len(chain)} intermediate(s) to {pkcs12_file_path}')
        try:
            atomic_write(pkcs12_file_path, build_pkcs12(selected['key'], leaf, chain, passphrase), 0o600, uid, gid)
        except FileNotFoundError as e:
            logging.error(f'Failed to write PKCS12 file to {pkcs12_file_path}, directory may not exist (Error: {e})')
            sys.exit(1)
        except PermissionError as e:
            logging.error(f'Failed to write or change ownership of file {pkcs12_file_path}, try running script with sudo (Error: {e})')
            sys.exit(1)
        logging.info(f'PKCS12 data written to {pkcs12_file_path}{" and encrypted" if passphrase else ""}')
    else:
        logging.info('PKCS12 file is already up to date')

    desired_config = {
        'customCertificateDomain': plex_hostname,
        'customCertificatePath': f'/config/{pkcs12_file_name}',
        'customCertificateKey': passphrase or '',
    }
    config_pending = bool(args.modify_plex_config and sync_plex_config(args.plex_config, desired_config, dry_run=True))

    if cert_changed or config_pending:
        container = get_plex_container(args.compose_project) if args.restart_plex else None
        if config_pending and container is not None:
            # Plex can rewrite Preferences.xml while running, so only edit it while Plex is stopped
            logging.warning(f'Stopping container ID: {container.short_id} to update the Plex config')
            container.stop(timeout=PLEX_STOP_TIMEOUT)
            try:
                sync_plex_config(args.plex_config, desired_config)
            finally:
                logging.warning(f'Starting container ID: {container.short_id}')
                container.start()
        else:
            if config_pending:
                sync_plex_config(args.plex_config, desired_config)
            if container is not None:
                logging.warning(f'Restarting container ID: {container.short_id}')
                container.restart(timeout=PLEX_STOP_TIMEOUT)
            else:
                logging.warning('Plex was not restarted, it will keep using its previous certificate and config until it is')
    else:
        logging.info('Nothing changed, doing nothing')

    stop_time = datetime.now()
    logging.info(f'{"=" * 15} Finished at {stop_time}, took {stop_time - start_time} {"=" * 15}')


if __name__ == '__main__':
    main()
