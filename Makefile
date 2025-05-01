SHELL := /bin/bash

.DEFAULT_GOAL:=help

DEFAULT_CONFS = vars/default/*.yml
ADVANCED_CONFS = roles/hmsdocker/defaults/main/*.yml

BASEDIR=$(shell pwd)

CUSTOM_CONF_DIR = inventory/group_vars/all

# Found and modified from: https://gist.github.com/Pierstoval/b2539c387c467c017bf2b0ace5a2e79b
# To use the "confirm" target inside another target,
# use the " if $(MAKE) -s confirm ; " syntax.
# The CI environment variable can be set to a non-empty string,
# it'll bypass this command that will "return true", as a "yes" answer.
confirm:
	REPLY="" ; \
	read -p "⚠ This will overwrite all existing files in '$(CUSTOM_CONF_DIR)', are you sure? [y/n] > " -r ; \
	if [[ ! $$REPLY =~ ^[Yy]$$ ]]; then \
		printf $(_ERROR) "FAIL" "Stopping" ; \
		exit 1; \
	else \
		printf $(_TITLE) "OK" "Copying files..." ; \
		exit 0; \
	fi
_WARN := "\033[33m[%s]\033[0m %s\n"  # Yellow text for "printf"
_TITLE := "\033[32m[%s]\033[0m %s\n" # Green text for "printf"
_ERROR := "\033[31m[%s]\033[0m %s\n" # Red text for "printf"

config:
	@if $(MAKE) -s confirm ; then \
		mkdir -p $(CUSTOM_CONF_DIR); \
		cp $(ADVANCED_CONFS) $(CUSTOM_CONF_DIR); \
		chmod 0600 $(CUSTOM_CONF_DIR)/*.yml; \
	fi

check: install-reqs
	@ansible-playbook -i inventory/hosts.yml hms-docker.yml --diff --check

apply: install-reqs
	@ansible-playbook -i inventory/hosts.yml hms-docker.yml --diff

install-reqs:
	@ansible-galaxy install -r galaxy-requirements.yml -p ./galaxy-roles

verify-containers:
	@sudo python3 .github/workflows/scripts/check_containers.py

update:
	@echo Updating from Git repo... && git pull
	@echo Updating variable names
	@echo Updating Traefik variables
	@sed -i 's\traefik_ext_hosts_configs_path:\hmsdocker_traefik_static_config_location:\g' $(CUSTOM_CONF_DIR)/traefik.yml
	@sed -i 's\hms_docker_library_path\hmsdocker_library_path\g' $(CUSTOM_CONF_DIR)/hmsd_advanced.yml
	@sed -i 's\transmission_vpn_provider:\hmsdocker_vpn_provider:\g' $(CUSTOM_CONF_DIR)/transmission.yml
	@sed -i 's\transmission_vpn_user:\hmsdocker_vpn_user:\g' $(CUSTOM_CONF_DIR)/transmission.yml
	@sed -i 's\transmission_vpn_pass:\hmsdocker_vpn_pass:\g' $(CUSTOM_CONF_DIR)/transmission.yml
	@sed -i 's\transmission_ovpn_config_local_path:\transmission_ovpn_config_local_dir:\g' $(CUSTOM_CONF_DIR)/transmission.yml
	@grep -q '^hmsdocker_vpn_type:' $(CUSTOM_CONF_DIR)/vpn.yml || echo "hmsdocker_vpn_type: ''" >> $(CUSTOM_CONF_DIR)/vpn.yml
	@echo Update finished

help:
	@echo make config :: copy default config files
	@echo make check :: check for any changes without doing anything \(diff\)
	@echo make apply :: apply any changes identified in the diff
	@echo make install-reqs :: installs ansible galaxy role requirements
	@echo make verify-containers :: checks containers exposed ports \(used in GitHub Actions\)
	@echo make update :: updates from the git repo and updates variable names \(if they were changed\)
