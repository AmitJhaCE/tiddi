#!/bin/bash

# Script to easily view logs for development
SERVICE=${1:-}

if [ -z "$SERVICE" ]; then
    echo "📋 Viewing logs for all services"
    echo "Press Ctrl+C to exit"
    echo ""
    docker-compose -f docker-compose.dev.yml logs -f --tail=50
else
    echo "📋 Viewing logs for service: $SERVICE"
    echo "Press Ctrl+C to exit"
    echo ""
    docker-compose -f docker-compose.dev.yml logs -f --tail=50 $SERVICE
fi