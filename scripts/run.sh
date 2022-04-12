#!/usr/bin/zsh
docker-compose pull && docker-compose up nginx fastapi certbot --no-build
