#!/bin/bash
cd sample_server/
APP_PORT=$1 docker compose -p "proj_$1" up