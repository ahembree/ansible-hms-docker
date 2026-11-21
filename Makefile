SHELL := /bin/bash

.DEFAULT_GOAL:=help

.PHONY: confirm config check apply install-reqs lint verify-containers manager update migrate-config _switch-branch switch-develop switch-stable branch help

ADVANCED_CONFS = roles/hmsdocker/defaults/main/*.yml

BASEDIR=$(shell pwd)

CUSTOM_CONF_DIR = inventory/group_vars/all

# Release channels: STABLE_BRANCH only moves when a release is cut,
# DEVELOP_BRANCH holds merged-but-unreleased changes.
# 'make update' pulls whichever branch is currently checked out.
STABLE_BRANCH = master
DEVELOP_BRANCH = develop
DEFAULT_CONTAINER_MAP = roles/hmsdocker/defaults/main/container_map.yml
# The playbook version, under its current name or the one releases up to v1.21 used
# ('make update' reads it both before and after pulling)
VERSION_QUERY = .[0].vars.hmsdocker_current_version // .[0].vars.hmsd_current_version
# Settings shared by Traefik and Caddy, moved out of traefik.yml by 'make update'
SHARED_PROXY_DEFAULTS = roles/hmsdocker/defaults/main/reverse_proxy.yml
# Where 'make update' keeps a copy of the config from before it changed it
CONF_BACKUP_DIR = backups

# No longer used by this Makefile, but DO NOT REMOVE: older Makefiles' 'make update'
# recipe keeps running after 'git pull' and greps this line out of the freshly
# pulled Makefile. Without it their first update silently skips the container map merge.
# The docs workflows publish the container map there under its old top-level key
# (hms_docker_container_map), which is the one those Makefiles look for.
REMOTE_CONFIG_URL = https://hmsdocker.dev/configs

VENV_DIR = .venv
VENV_PY = $(VENV_DIR)/bin/python3
# Marker file used to detect when requirements.txt changed since the last install
VENV_STAMP = $(VENV_DIR)/.requirements-installed

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
		cp roles/unifi_dns/defaults/main.yml $(CUSTOM_CONF_DIR)/unifi.yml; \
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
	@ansible-galaxy collection install community.docker community.general ansible.posix ansible.utils

# Needs ansible-lint installed (e.g. 'pipx install ansible-lint'), rules are in .ansible-lint
lint: install-reqs
	@ansible-lint

verify-containers:
	@sudo python3 .github/workflows/scripts/check_containers.py

manager:
	@set -e; \
	if [ -d "$(VENV_DIR)" ] && ! "$(VENV_PY)" -m pip --version > /dev/null 2>&1; then \
		if [ ! -w "$(VENV_DIR)" ]; then \
			printf $(_ERROR) "FAIL" "'$(VENV_DIR)' is incomplete and not writable by $$(id -un), remove it and re-run 'make manager':"; \
			printf $(_ERROR) "FAIL" "  sudo rm -rf $(VENV_DIR)"; \
			exit 1; \
		fi; \
		printf $(_WARN) "WARN" "Found an incomplete virtual environment in '$(VENV_DIR)', recreating it"; \
		rm -rf "$(VENV_DIR)"; \
	fi; \
	if [ ! -d "$(VENV_DIR)" ]; then \
		echo "Creating Python virtual environment"; \
		if ! python3 -m venv "$(VENV_DIR)"; then \
			rm -rf "$(VENV_DIR)"; \
			pyver=$$(python3 -c 'import sys; print("%d.%d" % sys.version_info[:2])' 2>/dev/null) || pyver=""; \
			printf $(_ERROR) "FAIL" "Could not create the Python virtual environment in '$(VENV_DIR)'"; \
			printf $(_ERROR) "FAIL" "On Debian/Ubuntu, install the venv module and re-run 'make manager':"; \
			if [ -n "$$pyver" ]; then \
				printf $(_ERROR) "FAIL" "  sudo apt install -y python3-venv python$$pyver-venv"; \
			else \
				printf $(_ERROR) "FAIL" "  sudo apt install -y python3 python3-venv"; \
			fi; \
			exit 1; \
		fi; \
	fi; \
	if [ ! -w "$(VENV_DIR)" ]; then \
		printf $(_WARN) "WARN" "'$(VENV_DIR)' is not writable by $$(id -un), skipping the requirements check"; \
		printf $(_WARN) "WARN" "If the settings manager fails to start, run 'sudo rm -rf $(VENV_DIR)' and try again"; \
	elif [ ! -f "$(VENV_STAMP)" ] || [ requirements.txt -nt "$(VENV_STAMP)" ]; then \
		echo "Installing Python requirements"; \
		piplog=$$(mktemp); \
		if ! "$(VENV_PY)" -m pip install -r requirements.txt > "$$piplog" 2>&1; then \
			cat "$$piplog"; \
			rm -f "$$piplog"; \
			printf $(_ERROR) "FAIL" "Failed to install Python requirements from requirements.txt"; \
			exit 1; \
		fi; \
		rm -f "$$piplog"; \
		touch "$(VENV_STAMP)" 2>/dev/null || \
			printf $(_WARN) "WARN" "Could not write to '$(VENV_DIR)', requirements will be re-checked on every run"; \
	fi
	@$(VENV_PY) settings_manager.py

update: $(YQ_LOCAL)
	@echo "Version Before: $$($(YQ_LOCAL) '$(VERSION_QUERY)' hms-docker.yml)"
	@branch=$$(git symbolic-ref --short -q HEAD) || { \
		printf $(_ERROR) "FAIL" "Not on a branch (detached HEAD). Run 'make switch-stable' or 'make switch-develop' first."; \
		exit 1; \
	}; \
	if [ "$$branch" = "$(STABLE_BRANCH)" ]; then \
		printf $(_TITLE) "INFO" "Release channel: stable ($$branch)"; \
	elif [ "$$branch" = "$(DEVELOP_BRANCH)" ]; then \
		printf $(_WARN) "INFO" "Release channel: develop ($$branch) - includes unreleased changes"; \
	else \
		printf $(_WARN) "WARN" "On non-channel branch '$$branch', pulling 'origin/$$branch'"; \
	fi; \
	echo "Updating from Git repo..." && git pull origin "$$branch" -q
	@# Re-invoke make so the rest runs from the freshly pulled Makefile, migrations and container map
	@$(MAKE) -s migrate-config

# Applies variable renames (keys and the references to them, see migrations/apply_renames.py)
# and merges new container map services/keys into the user's config, using the migrations
# and default container map of the branch that is checked out (so they always match the
# code that will be applied).
migrate-config: $(YQ_LOCAL)
	@# Snapshot the config. If this run changes it, the snapshot is kept as a backup (see the end of this recipe),
	@# e.g. to restore the old variable names after switching back to a branch that does not know the new ones
	@rm -rf "$(CONF_BACKUP_DIR)/.pending"; \
	if ls $(CUSTOM_CONF_DIR)/*.yml >/dev/null 2>&1; then \
		mkdir -p "$(CONF_BACKUP_DIR)/.pending" && chmod 700 "$(CONF_BACKUP_DIR)" && cp -p $(CUSTOM_CONF_DIR)/*.yml "$(CONF_BACKUP_DIR)/.pending/"; \
	fi
	@echo "Applying variable renames from migrations/variable_renames.yml..."
	@python3 migrations/apply_renames.py $(CUSTOM_CONF_DIR)

	@# The settings Traefik shares with Caddy moved from traefik.yml to reverse_proxy.yml. Move them in the inventory
	@# too: group_vars files load in alphabetical order, so values left in traefik.yml would override reverse_proxy.yml
	@src="$(CUSTOM_CONF_DIR)/traefik.yml"; dst="$(CUSTOM_CONF_DIR)/reverse_proxy.yml"; \
	[ -f "$$src" ] || exit 0; \
	shared=$$($(YQ_LOCAL) -r 'keys | .[]' "$(SHARED_PROXY_DEFAULTS)"); \
	moving=""; \
	for key in $$shared; do \
		if [ "$$($(YQ_LOCAL) eval 'has("'$$key'")' "$$src" 2>/dev/null)" = "true" ]; then moving="$$moving $$key"; fi; \
	done; \
	[ -n "$$moving" ] || exit 0; \
	echo "Moving the settings shared by Traefik and Caddy from traefik.yml to reverse_proxy.yml..."; \
	created=0; \
	if [ ! -f "$$dst" ]; then \
		cp "$(SHARED_PROXY_DEFAULTS)" "$$dst" && chmod 0600 "$$dst"; \
		created=1; \
		for key in $$shared; do \
			case " $$moving " in *" $$key "*) ;; *) $(YQ_LOCAL) eval -i 'del(."'$$key'")' "$$dst" ;; esac; \
		done; \
	fi; \
	for key in $$moving; do \
		if [ "$$created" = 0 ] && [ "$$($(YQ_LOCAL) eval 'has("'$$key'")' "$$dst" 2>/dev/null)" = "true" ]; then \
			printf $(_WARN) "WARN" "$$key is set in both traefik.yml and reverse_proxy.yml, the value in traefik.yml is used (it loads later). Remove it from one of them"; \
			continue; \
		fi; \
		if $(YQ_LOCAL) eval -i '."'$$key'" = load("'"$$src"'")."'$$key'"' "$$dst" \
			&& [ "$$($(YQ_LOCAL) -o=json '."'$$key'"' "$$dst")" = "$$($(YQ_LOCAL) -o=json '."'$$key'"' "$$src")" ]; then \
			$(YQ_LOCAL) eval -i 'del(."'$$key'")' "$$src"; \
			echo "  moved $$key"; \
		else \
			printf $(_WARN) "WARN" "Could not copy $$key to reverse_proxy.yml, it stays in traefik.yml"; \
		fi; \
	done

	@# The per-container `traefik` key of the container map was renamed to `proxy`, in every file that defines the map
	@for f in $(CUSTOM_CONF_DIR)/*.yml; do \
		[ -f "$$f" ] || continue; \
		[ "$$($(YQ_LOCAL) eval '.hmsdocker_container_map | tag == "!!map"' "$$f" 2>/dev/null)" = "true" ] || continue; \
		$(YQ_LOCAL) -r '.hmsdocker_container_map | to_entries | .[] | select(.value | tag == "!!map") | select(.value | has("traefik")) | .key' "$$f" | while read service; do \
			hasproxy=$$($(YQ_LOCAL) eval '.hmsdocker_container_map."'$$service'" | has("proxy")' "$$f"); \
			if [ "$$hasproxy" = "true" ]; then \
				$(YQ_LOCAL) eval -i 'del(.hmsdocker_container_map."'$$service'".traefik)' "$$f"; \
				echo "  $$service: removed traefik in $$(basename "$$f"), it already has proxy"; \
			else \
				$(YQ_LOCAL) eval -i '(.hmsdocker_container_map."'$$service'".traefik | key) = "proxy"' "$$f"; \
				echo "  renamed $$service.traefik -> $$service.proxy in $$(basename "$$f")"; \
			fi; \
		done; \
	done

	@if [ ! -f "$(CUSTOM_CONF_DIR)/container_map.yml" ]; then \
		echo "No $(CUSTOM_CONF_DIR)/container_map.yml found, skipping container map merge (run 'make config' first)"; \
		exit 0; \
	fi; \
	srcfile="$(DEFAULT_CONTAINER_MAP)"; \
	echo "Merging container map updates from $$srcfile..."; \
	echo Checking for new services...; \
	$(YQ_LOCAL) -r '.hmsdocker_container_map | keys | .[]' "$$srcfile" | while read service; do \
		exists=$$($(YQ_LOCAL) eval ".hmsdocker_container_map | has(\"$$service\")" "$(CUSTOM_CONF_DIR)/container_map.yml"); \
		if [ "$$exists" = "false" ]; then \
			echo "Adding missing service: $$service"; \
			$(YQ_LOCAL) eval -i '.hmsdocker_container_map."'$$service'" = load("'"$$srcfile"'").hmsdocker_container_map."'$$service'"' "$(CUSTOM_CONF_DIR)/container_map.yml"; \
		else \
			$(YQ_LOCAL) -r ".hmsdocker_container_map.$$service | keys | .[]" "$$srcfile" | while read key; do \
				existskey=$$($(YQ_LOCAL) eval ".hmsdocker_container_map.$$service | has(\"$$key\")" "$(CUSTOM_CONF_DIR)/container_map.yml"); \
				if [ "$$existskey" = "false" ]; then \
					echo "Adding missing key: $$service.$$key"; \
					$(YQ_LOCAL) eval -i '.hmsdocker_container_map."'$$service'"."'$$key'" = load("'"$$srcfile"'").hmsdocker_container_map."'$$service'"."'$$key'"' "$(CUSTOM_CONF_DIR)/container_map.yml"; \
				fi; \
			done; \
		fi; \
	done; \
	echo Coalescing service controls...; \
	$(YQ_LOCAL) -r '.hmsdocker_container_map | keys | .[]' "$$srcfile" | while read service; do \
		remote_keys=$$($(YQ_LOCAL) -r '.hmsdocker_container_map."'$$service'" | keys | .[]' "$$srcfile"); \
		local_keys=$$($(YQ_LOCAL) -r '.hmsdocker_container_map."'$$service'" | keys | .[]' "$(CUSTOM_CONF_DIR)/container_map.yml"); \
		for key in $$local_keys; do \
			if ! echo "$$remote_keys" | grep -qx "$$key"; then \
				echo "Deleting obsolete key: $$service.$$key"; \
				$(YQ_LOCAL) eval -i 'del(.hmsdocker_container_map."'$$service'"."'$$key'")' "$(CUSTOM_CONF_DIR)/container_map.yml"; \
			fi; \
		done; \
	done; \
	remote_services=$$($(YQ_LOCAL) -r '.hmsdocker_container_map | keys | .[]' "$$srcfile"); \
	for service in $$($(YQ_LOCAL) -r '.hmsdocker_container_map | keys | .[]' "$(CUSTOM_CONF_DIR)/container_map.yml"); do \
		if ! echo "$$remote_services" | grep -qx "$$service"; then \
			printf $(_WARN) "WARN" "Service '$$service' in your container_map.yml does not exist on this branch, disable or remove it before running 'make apply'"; \
		fi; \
	done; \
	$(YQ_LOCAL) eval -i 'sort_keys(.hmsdocker_container_map)' "$(CUSTOM_CONF_DIR)/container_map.yml"; \
	echo "Update finished"
	@pending="$(CONF_BACKUP_DIR)/.pending"; \
	[ -d "$$pending" ] || exit 0; \
	changed=0; \
	for f in $(CUSTOM_CONF_DIR)/*.yml; do \
		[ -f "$$f" ] || continue; \
		cmp -s "$$f" "$$pending/$$(basename "$$f")" || changed=1; \
	done; \
	for f in "$$pending"/*.yml; do \
		[ -f "$(CUSTOM_CONF_DIR)/$$(basename "$$f")" ] || changed=1; \
	done; \
	if [ "$$changed" = 1 ]; then \
		backup="$(CONF_BACKUP_DIR)/inventory-$$(date +%Y%m%d-%H%M%S)"; \
		mv "$$pending" "$$backup"; \
		printf $(_TITLE) "INFO" "Your config from before this update is saved in $$backup"; \
		echo "  To go back to it (e.g. after 'make switch-stable' to a release without these changes):"; \
		echo "  rm $(CUSTOM_CONF_DIR)/*.yml && cp -p $$backup/*.yml $(CUSTOM_CONF_DIR)/"; \
	else \
		rm -rf "$$pending"; \
	fi
	@echo "Version Now: $$($(YQ_LOCAL) '$(VERSION_QUERY)' hms-docker.yml)"

# Checks out a release channel branch (creating a local tracking branch if it
# doesn't exist yet) and then runs 'make update' on it.
# Usage: $(MAKE) -s _switch-branch TARGET=<branch>
_switch-branch:
	@# Explicit refspec so this also works for clones made with --single-branch
	@git fetch -q origin "+refs/heads/$(TARGET):refs/remotes/origin/$(TARGET)"
	@# Local edits (e.g. inventory/hosts.yml for a remote host) are carried over;
	@# git only refuses if an edited file also differs between the two branches.
	@if git show-ref --verify --quiet "refs/heads/$(TARGET)"; then \
		git checkout -q "$(TARGET)"; \
	else \
		git checkout -q -b "$(TARGET)" --track "origin/$(TARGET)"; \
	fi || { \
		printf $(_ERROR) "FAIL" "Could not switch to '$(TARGET)', commit or stash the local changes listed above and try again"; \
		exit 1; \
	}
	@printf $(_TITLE) "OK" "Switched to '$(TARGET)'"
	@$(MAKE) -s update

switch-develop:
	@printf $(_WARN) "WARN" "The '$(DEVELOP_BRANCH)' branch contains changes that have not been released yet and may be unstable."
	@REPLY="" ; \
	read -p "Switch to the '$(DEVELOP_BRANCH)' branch? [y/n] > " -r ; \
	if [[ ! $$REPLY =~ ^[Yy]$$ ]]; then \
		printf $(_ERROR) "FAIL" "Stopping"; \
		exit 1; \
	fi
	@$(MAKE) -s _switch-branch TARGET=$(DEVELOP_BRANCH)

switch-stable:
	@if [ "$$(git symbolic-ref --short -q HEAD)" = "$(DEVELOP_BRANCH)" ]; then \
		printf $(_WARN) "WARN" "Moving from '$(DEVELOP_BRANCH)' to '$(STABLE_BRANCH)' rolls back any unreleased changes."; \
		printf $(_WARN) "WARN" "Services that only exist on '$(DEVELOP_BRANCH)' will be flagged below, review them before 'make apply'."; \
	fi
	@$(MAKE) -s _switch-branch TARGET=$(STABLE_BRANCH)

branch:
	@echo "Current branch: $$(git symbolic-ref --short -q HEAD || echo 'detached HEAD')"
	@echo "Playbook version: $$(grep -oP 'hmsd(ocker)?_current_version:\s*"\K[^"]+' hms-docker.yml)"

help:
	@echo make config :: copy default config files
	@echo make check :: check for any changes without doing anything \(diff\)
	@echo make apply :: apply any changes identified in the diff
	@echo make install-reqs :: installs ansible galaxy role and collection requirements
	@echo make lint :: runs ansible-lint \(used in GitHub Actions\)
	@echo make migrate-config :: renames deprecated variables in your config and adds new container map entries
	@echo make verify-containers :: checks containers exposed ports \(used in GitHub Actions\)
	@echo make update :: updates from the git repo \(current branch\) and updates variable names \(if they were changed\)
	@echo make switch-develop :: switch to the develop branch \(unreleased changes\) and update
	@echo make switch-stable :: switch to the stable master branch \(latest release\) and update
	@echo make branch :: show the current branch and playbook version
