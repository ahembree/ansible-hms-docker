SHELL := /bin/bash

.DEFAULT_GOAL:=help

DEFAULT_CONFS = vars/default/*.yml
ADVANCED_CONFS = roles/hmsdocker/defaults/main/*.yml

BASEDIR=$(shell pwd)

CUSTOM_CONF_DIR = inventory/group_vars/all

REMOTE_CONFIG_URL = https://hmsdocker.dev/configs

ARCH = $(shell uname -m)
BIN_DIR = ./bin
YQ_LOCAL = $(BIN_DIR)/yq
# Pick binary URL based on architecture
ifeq ($(ARCH),x86_64)
  YQ_URL = https://github.com/mikefarah/yq/releases/latest/download/yq_linux_amd64
else ifeq ($(ARCH),aarch64)
  YQ_URL = https://github.com/mikefarah/yq/releases/latest/download/yq_linux_arm64
else ifeq ($(ARCH),arm64)
  YQ_URL = https://github.com/mikefarah/yq/releases/latest/download/yq_linux_arm64
else ifeq ($(ARCH),armv7l)
  YQ_URL = https://github.com/mikefarah/yq/releases/latest/download/yq_linux_arm
else ifeq ($(ARCH),armhf)
  YQ_URL = https://github.com/mikefarah/yq/releases/latest/download/yq_linux_arm
else
  $(error Unsupported architecture: $(ARCH))
endif

# Install local unrestricted yq
$(YQ_LOCAL):
	@mkdir -p $(BIN_DIR)
	@echo "Detected architecture: $(ARCH)"
	@echo "Downloading yq from: $(YQ_URL)"
	@wget -qO $(YQ_LOCAL) $(YQ_URL)
	@chmod +x $(YQ_LOCAL)

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
	@echo > logs/hms-docker.log
	@ansible-playbook -i inventory/hosts.yml hms-docker.yml --diff --check

apply: install-reqs
	@echo > logs/hms-docker.log
	@ansible-playbook -i inventory/hosts.yml hms-docker.yml --diff

install-reqs:
	@ansible-galaxy install -r galaxy-requirements.yml -p ./galaxy-roles

verify-containers:
	@sudo python3 .github/workflows/scripts/check_containers.py

update: $(YQ_LOCAL)
	@echo "Updating from Git repo..." && git pull
	@echo "Updating variables..."
	@sed -i 's\traefik_ext_hosts_configs_path:\hmsdocker_traefik_static_config_location:\g' $(CUSTOM_CONF_DIR)/traefik.yml
	@sed -i 's\hms_docker_library_path\hmsdocker_library_path\g' $(CUSTOM_CONF_DIR)/hmsd_advanced.yml
	@sed -i 's\transmission_vpn_provider:\hmsdocker_vpn_provider:\g' $(CUSTOM_CONF_DIR)/transmission.yml
	@sed -i 's\transmission_vpn_user:\hmsdocker_vpn_user:\g' $(CUSTOM_CONF_DIR)/transmission.yml
	@sed -i 's\transmission_vpn_pass:\hmsdocker_vpn_pass:\g' $(CUSTOM_CONF_DIR)/transmission.yml
	@sed -i 's\transmission_ovpn_config_local_path:\transmission_ovpn_config_local_dir:\g' $(CUSTOM_CONF_DIR)/transmission.yml
	@grep -q '^hmsdocker_vpn_type:' $(CUSTOM_CONF_DIR)/vpn.yml || echo "hmsdocker_vpn_type: ''" >> $(CUSTOM_CONF_DIR)/vpn.yml

	@echo "Fetching container map updates from $(REMOTE_CONFIG_URL)/container_map.yml..."
	@tmpfile=$$(mktemp); \
	curl -s "$(REMOTE_CONFIG_URL)/container_map.yml" > "$$tmpfile"; \
	echo Checking for new services...; \
	$(YQ_LOCAL) -r '.hms_docker_container_map | keys | .[]' "$$tmpfile" | while read service; do \
		exists=$$($(YQ_LOCAL) eval ".hms_docker_container_map | has(\"$$service\")" "$(CUSTOM_CONF_DIR)/container_map.yml"); \
		if [ "$$exists" = "false" ]; then \
			echo "Adding missing service: $$service"; \
			$(YQ_LOCAL) eval -i '.hms_docker_container_map."'$$service'" = load("'"$$tmpfile"'").hms_docker_container_map."'$$service'"' "$(CUSTOM_CONF_DIR)/container_map.yml"; \
		else \
			$(YQ_LOCAL) -r ".hms_docker_container_map.$$service | keys | .[]" "$$tmpfile" | while read key; do \
				existskey=$$($(YQ_LOCAL) eval ".hms_docker_container_map.$$service | has(\"$$key\")" "$(CUSTOM_CONF_DIR)/container_map.yml"); \
				if [ "$$existskey" = "false" ]; then \
					echo "Adding missing key: $$service.$$key"; \
					$(YQ_LOCAL) eval -i '.hms_docker_container_map."'$$service'"."'$$key'" = load("'"$$tmpfile"'").hms_docker_container_map."'$$service'"."'$$key'"' "$(CUSTOM_CONF_DIR)/container_map.yml"; \
				fi; \
			done; \
		fi; \
	done; \
	echo Coalescing service controls...; \
	$(YQ_LOCAL) -r '.hms_docker_container_map | keys | .[]' "$$tmpfile" | while read service; do \
		remote_keys=$$($(YQ_LOCAL) -r '.hms_docker_container_map."'$$service'" | keys | .[]' "$$tmpfile"); \
		local_keys=$$($(YQ_LOCAL) -r '.hms_docker_container_map."'$$service'" | keys | .[]' "$(CUSTOM_CONF_DIR)/container_map.yml"); \
		for key in $$local_keys; do \
			if ! echo "$$remote_keys" | grep -qx "$$key"; then \
				echo "Deleting obsolete key: $$service.$$key"; \
				$(YQ_LOCAL) eval -i 'del(.hms_docker_container_map."'$$service'"."'$$key'")' "$(CUSTOM_CONF_DIR)/container_map.yml"; \
			fi; \
		done; \
	done; \
	$(YQ_LOCAL) eval -i 'sort_keys(.hms_docker_container_map)' "$(CUSTOM_CONF_DIR)/container_map.yml"; \
	rm -f "$$tmpfile"; \
	echo "Update finished"

help:
	@echo make config :: copy default config files
	@echo make check :: check for any changes without doing anything \(diff\)
	@echo make apply :: apply any changes identified in the diff
	@echo make install-reqs :: installs ansible galaxy role requirements
	@echo make verify-containers :: checks containers exposed ports \(used in GitHub Actions\)
	@echo make update :: updates from the git repo and updates variable names \(if they were changed\)
