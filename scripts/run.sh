#!/usr/bin/zsh
docker-compose pull && docker-compose up --no-build nginx fastapi certbot
