#!/bin/bash

# Function to display usage
usage() {
    echo "Usage: $0 [start|stop|restart|status|logs]"
    exit 1
}

# Function to start services
start_services() {
    echo "Starting services..."
    docker-compose up -d
    echo "Services started. Access Flower at http://localhost:5555"
}

# Function to stop services
stop_services() {
    echo "Stopping services..."
    docker-compose down
    echo "Services stopped"
}

# Function to restart services
restart_services() {
    stop_services
    start_services
}

# Function to show service status
show_status() {
    echo "Service Status:"
    docker-compose ps
}

# Function to show logs
show_logs() {
    echo "Showing logs (Ctrl+C to exit)..."
    docker-compose logs -f
}

# Main script logic
case "$1" in
    start)
        start_services
        ;;
    stop)
        stop_services
        ;;
    restart)
        restart_services
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs
        ;;
    *)
        usage
        ;;
esac 