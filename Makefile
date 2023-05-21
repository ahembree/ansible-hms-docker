.DEFAULT_GOAL:=help

DEFAULT_CONFS = vars/default/*.yml
ADVANCED_CONFS = roles/hmsdocker/defaults/main/*.yml

CUSTOM_CONF_DIR = vars/custom

basic:
	@mkdir -p $(CUSTOM_CONF_DIR)
	@cp -n $(DEFAULT_CONFS) $(CUSTOM_CONF_DIR)

advanced:
	@mkdir -p $(CUSTOM_CONF_DIR)
	@cp -n $(ADVANCED_CONFS) $(CUSTOM_CONF_DIR)

help:
	@echo make basic :: for a basic config
	@echo make advanced :: for an advanced config
