#!/bin/bash

source ./0.config-script.sh
docker run -it --rm \
    -v ${PWD}/en/api-gateway/sample-app.py:/app/app.py \
    -v ${PWD}/common/example/.chalice:/app/.chalice \
    -v ${PWD}/common/example/chalicelib:/app/chalicelib \
    -v ${PWD}/../chalice_spec:/app/chalice_spec \
    -p 8000:8000 \
    $CHALICE_SPEC_IMAGE "/bin/sh"
