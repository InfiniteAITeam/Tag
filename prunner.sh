#!/bin/bash

set +x

AVAILABLE_OPTIONS="bbix, taggerxup, appup"

if [ $# -eq 0 ]; then
    echo "Error: No command provided. "
    echo "prunner.sh <command> <proj-name>"
    echo "Available commands: ${AVAILABLE_OPTIONS}"
    echo ""
    echo "Commands:"
    echo "  bbix        - creates the base docker image ci/taggerxvfb"
    echo "  taggerxup   - starts the tagger service with xvfb (requires proj-name)"
    echo "  appup       - starts the backend API service (requires proj-name)"
    echo ""
    echo "Parameters:"
    echo "  proj-name   - docker compose project name to isolate multiple instances"
    echo "                ensure that proj-name is consistent between taggerxup and appup"
    echo ""
    echo "Examples:"
    echo "  prunner.sh bbix"
    echo "  prunner.sh taggerxup my-project"
    echo "  prunner.sh appup my-project"
    exit 1
fi

# Validate docker installation
if ! command -v docker &> /dev/null; then
    echo "Error: docker is not installed or not in PATH"
    exit 1
fi

# Validate docker-compose installation (supports both docker-compose and docker compose)
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "Error: docker-compose is not installed or not in PATH"
    exit 1
fi

# Use docker compose if docker-compose is not available
if command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE="docker-compose"
else
    DOCKER_COMPOSE="docker compose"
fi

COMMAND=${1}
shift

case "$COMMAND" in
    taggerxup)
        PROJECT_NAME=${1}
        if [[ -z "${PROJECT_NAME}" ]]; then
            echo "Error: proj-name is required for taggerxup command"
            echo "Usage: prunner.sh taggerxup <proj-name>"
            exit 1
        fi
        echo "Starting tagger service with project name: ${PROJECT_NAME}"
        echo "Using docker compose: ${DOCKER_COMPOSE}"
        $DOCKER_COMPOSE -f docker-compose-taggerx.yml -p ${PROJECT_NAME} up --build --abort-on-container-failure
        ;;
    appup)
        PROJECT_NAME=${1}
        if [[ -z "${PROJECT_NAME}" ]]; then
            echo "Error: proj-name is required for appup command"
            echo "Usage: prunner.sh appup <proj-name>"
            exit 1
        fi
        echo "Starting backend API service with project name: ${PROJECT_NAME}"
        echo "Using docker compose: ${DOCKER_COMPOSE}"
        $DOCKER_COMPOSE -f docker-compose-app.yml -p ${PROJECT_NAME} up --build --abort-on-container-failure
        ;;
    bbix)
        echo "Building base docker image ci/taggerxvfb..."
        if [ ! -d "base-docker/v1" ]; then
            echo "Error: base-docker/v1 directory not found"
            exit 1
        fi
        if [ ! -f "base-docker/v1/bbixvfb.sh" ]; then
            echo "Error: base-docker/v1/bbixvfb.sh script not found"
            exit 1
        fi
        cd base-docker/v1 && chmod +x ./bbixvfb.sh && ./bbixvfb.sh
        ;;
    *)
        echo "Error: unrecognized command '${COMMAND}'"
        echo "Available commands: ${AVAILABLE_OPTIONS}"
        exit 1
        ;;
esac
