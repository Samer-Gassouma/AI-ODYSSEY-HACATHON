#!/bin/bash

case "$1" in
  "build")
    docker-compose build
    ;;
  "up")
    docker-compose up
    ;;
  "restart")
    docker-compose restart
    ;;
  "rebuild")
    docker-compose up --build
    ;;
  *)
    echo "Usage: ./docker.sh [build|up|restart|rebuild]"
    echo "  build   - Build the images"
    echo "  up      - Start containers"
    echo "  restart - Restart containers"
    echo "  rebuild - Rebuild and start containers"
    ;;
esac
