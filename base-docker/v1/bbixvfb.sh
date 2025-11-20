#!/bin/sh
set +x
# start a subshell
export ROOTDIR=${PWD}
(
set +x
cd  ${ROOTDIR}/taggerxvfb
docker build --tag ait/taggerxvfb .
)

