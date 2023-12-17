#!/bin/bash

TARGET=en/api-gateway

source ./0.config-script.sh
docker run -it --rm \
    -v ${PWD}/${TARGET}/sample-app.py:/app/app.py \
    -v ${PWD}/${TARGET}/.chalice:/app/.chalice \
    -v ${PWD}/common/example/chalicelib:/app/chalicelib \
    -v ${PWD}/../chalice_spec:/app/vendor/chalice_spec \
    --env-file ${PWD}/.env \
    --entrypoint "/usr/local/bin/chalice" \
    $CHALICE_SPEC_IMAGE deploy
