#!/bin/bash
echo "Starting SOMS with Virtual Edge Simulation..."

# Check Docker
if ! command -v docker &> /dev/null
then
    echo "Docker could not be found."
    exit
fi

# Build & Run with Override
docker-compose -f ../docker-compose.yml -f ../docker-compose.edge-mock.yml up --build -d

echo "Virtual Edge Started. View logs with: 'docker logs -f soms-virtual-edge'"
