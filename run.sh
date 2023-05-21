#!/bin/bash

if [[ ! -n $1 ]];
then
    echo "You must specify either \"apply\" or \"check\"."
else
    if [[ $1 = "apply" ]];
    then
        ansible-playbook -i inventory --connection local hms-docker.yml --diff
    elif [[ $1 == "check" ]];
    then
        ansible-playbook -i inventory --connection local hms-docker.yml --diff --check
    fi
fi
