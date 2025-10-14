#!/bin/bash

# SuperTube Launch Script
# Checks prerequisites and launches the application

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored messages
print_error() {
    echo -e "${RED}❌ Error: $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  Warning: $1${NC}"
}

# Check if Docker is installed
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed"
        echo "Please install Docker from: https://docs.docker.com/get-docker/"
        exit 1
    fi
    print_success "Docker found"
}

# Check if Docker Compose is installed
check_docker_compose() {
    # Check for docker-compose (v1) or docker compose (v2)
    if command -v docker-compose &> /dev/null; then
        DOCKER_COMPOSE="docker-compose"
    elif docker compose version &> /dev/null; then
        DOCKER_COMPOSE="docker compose"
    else
        print_error "Docker Compose is not installed"
        echo "Please install Docker Compose from: https://docs.docker.com/compose/install/"
        exit 1
    fi
    print_success "Docker Compose found ($DOCKER_COMPOSE)"
}

# Check if Docker daemon is running
check_docker_daemon() {
    if ! docker info &> /dev/null; then
        print_error "Docker daemon is not running"
        echo "Please start Docker and try again"
        exit 1
    fi
    print_success "Docker daemon is running"
}

# Check if config.yaml exists
check_config() {
    if [ ! -f "config/config.yaml" ]; then
        print_warning "config.yaml not found"
        echo ""
        echo "Please create your configuration:"
        echo "  1. Copy the example: cp config/config.yaml.example config/config.yaml"
        echo "  2. Edit config/config.yaml and add your YouTube channel IDs"
        echo ""
        read -p "Press Enter to continue anyway (will show error in app)..."
        return 1
    fi
    print_success "config.yaml found"
    return 0
}

# Check if credentials.json exists
check_credentials() {
    if [ ! -f "config/credentials.json" ]; then
        print_warning "credentials.json not found"
        echo ""
        echo "Please download OAuth2 credentials from Google Cloud Console:"
        echo "  1. Go to: https://console.cloud.google.com/"
        echo "  2. Create OAuth 2.0 credentials (Desktop app)"
        echo "  3. Download the JSON file"
        echo "  4. Save it as: config/credentials.json"
        echo ""
        echo "See README.md for detailed instructions."
        echo ""
        read -p "Press Enter to continue anyway (will show error in app)..."
        return 1
    fi
    print_success "credentials.json found"
    return 0
}

# Build Docker image if needed
build_image() {
    if [ "$1" == "--rebuild" ] || ! docker images | grep -q "supertube"; then
        print_info "Building Docker image..."
        $DOCKER_COMPOSE build
        print_success "Docker image built"
    else
        print_info "Using existing Docker image (use --rebuild to force rebuild)"
    fi
}

# Main script
main() {
    echo ""
    echo "╔═══════════════════════════════════════╗"
    echo "║     SuperTube - YouTube Stats TUI    ║"
    echo "╚═══════════════════════════════════════╝"
    echo ""

    # Check all prerequisites
    print_info "Checking prerequisites..."
    check_docker
    check_docker_compose
    check_docker_daemon

    echo ""
    print_info "Checking configuration..."
    CONFIG_OK=$(check_config && echo "1" || echo "0")
    CREDS_OK=$(check_credentials && echo "1" || echo "0")

    # Exit if both config and credentials are missing
    if [ "$CONFIG_OK" == "0" ] && [ "$CREDS_OK" == "0" ]; then
        echo ""
        print_error "Both configuration and credentials are missing"
        echo "Cannot continue. Please set up the application first."
        echo "See README.md for instructions."
        exit 1
    fi

    echo ""
    # Build image
    build_image "$1"

    echo ""
    print_info "Starting SuperTube..."
    echo ""
    print_info "Keyboard shortcuts:"
    echo "  - Press 'q' to quit"
    echo "  - Press 'r' to refresh"
    echo "  - Press '?' for help"
    echo ""

    # Launch the application
    $DOCKER_COMPOSE run --rm supertube

    # Clean exit
    echo ""
    print_success "SuperTube exited successfully"
}

# Handle Ctrl+C gracefully
trap 'echo ""; print_warning "Interrupted by user"; exit 130' INT

# Run main script with all arguments
main "$@"
