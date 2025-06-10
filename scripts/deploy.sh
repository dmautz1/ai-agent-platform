#!/bin/bash

# AI Agent Platform - Unified Deployment Script for DigitalOcean App Platform
# Version: 1.0
# Description: Automated deployment script with comprehensive error handling and monitoring

set -e  # Exit on any error

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DEPLOYMENT_CONFIG="$PROJECT_ROOT/.do/app.yaml"
ENV_FILE="$PROJECT_ROOT/.env"
LOG_FILE="/tmp/ai-agent-deploy-$(date +%Y%m%d-%H%M%S).log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Deployment configuration
APP_NAME=""
ENVIRONMENT=""
DOMAIN=""
FORCE_CREATE=false
SKIP_BUILD=false
SKIP_ENV_CHECK=false
DRY_RUN=false
VERBOSE=false

# Log function
log() {
    local level=$1
    shift
    local message="$@"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    case $level in
        "INFO")
            echo -e "${GREEN}[INFO]${NC} $message" | tee -a "$LOG_FILE"
            ;;
        "WARN")
            echo -e "${YELLOW}[WARN]${NC} $message" | tee -a "$LOG_FILE"
            ;;
        "ERROR")
            echo -e "${RED}[ERROR]${NC} $message" | tee -a "$LOG_FILE"
            ;;
        "DEBUG")
            if [ "$VERBOSE" = true ]; then
                echo -e "${BLUE}[DEBUG]${NC} $message" | tee -a "$LOG_FILE"
            fi
            ;;
        "SUCCESS")
            echo -e "${GREEN}[SUCCESS]${NC} $message" | tee -a "$LOG_FILE"
            ;;
    esac
}

# Progress indicator
show_progress() {
    local task="$1"
    local duration=${2:-3}
    
    echo -n -e "${CYAN}$task${NC}"
    for i in $(seq 1 $duration); do
        sleep 1
        echo -n "."
    done
    echo ""
}

# Usage information
show_usage() {
    cat << EOF
AI Agent Platform - DigitalOcean Deployment Script v1.0

USAGE:
    $0 [OPTIONS] [COMMAND]

COMMANDS:
    deploy          Deploy or update the application (default)
    create          Create a new app (force creation even if app exists)
    update          Update existing app configuration
    status          Check deployment status
    logs            View application logs
    rollback        Rollback to previous deployment
    destroy         Destroy the application (with confirmation)
    validate        Validate configuration without deploying

OPTIONS:
    -n, --name NAME         App name (default: from app.yaml)
    -e, --env ENV          Environment (development|staging|production)
    -d, --domain DOMAIN    Custom domain
    --force-create         Force create new app (destroys existing)
    --skip-build          Skip frontend build step
    --skip-env-check      Skip environment variable validation
    --dry-run             Show what would be done without executing
    -v, --verbose         Enable verbose logging
    -h, --help            Show this help message

EXAMPLES:
    $0 deploy --env production --domain yourdomain.com
    $0 create --name my-ai-agent --env staging
    $0 status
    $0 logs backend
    $0 validate --env production

ENVIRONMENT VARIABLES:
    Required:
        SUPABASE_URL            Supabase project URL
        SUPABASE_KEY            Supabase anon key
        SUPABASE_SERVICE_KEY    Supabase service key
        GOOGLE_API_KEY          Google AI API key
        JWT_SECRET              JWT secret key
    
    Optional:
        GITHUB_REPO             GitHub repository (user/repo)
        TRUSTED_HOSTS           Comma-separated trusted hosts
        ALLOWED_ORIGINS         Comma-separated CORS origins

For detailed setup instructions, see: DEPLOYMENT_GUIDE.md
EOF
}

# Parse command line arguments
parse_args() {
    COMMAND="deploy"
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            -n|--name)
                APP_NAME="$2"
                shift 2
                ;;
            -e|--env)
                ENVIRONMENT="$2"
                shift 2
                ;;
            -d|--domain)
                DOMAIN="$2"
                shift 2
                ;;
            --force-create)
                FORCE_CREATE=true
                shift
                ;;
            --skip-build)
                SKIP_BUILD=true
                shift
                ;;
            --skip-env-check)
                SKIP_ENV_CHECK=true
                shift
                ;;
            --dry-run)
                DRY_RUN=true
                shift
                ;;
            -v|--verbose)
                VERBOSE=true
                shift
                ;;
            -h|--help)
                show_usage
                exit 0
                ;;
            deploy|create|update|status|logs|rollback|destroy|validate)
                COMMAND="$1"
                shift
                ;;
            *)
                log "ERROR" "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done
}

# Check prerequisites
check_prerequisites() {
    log "INFO" "Checking deployment prerequisites..."
    
    # Check if doctl is installed
    if ! command -v doctl &> /dev/null; then
        log "ERROR" "doctl CLI is not installed. Please install it first:"
        log "ERROR" "  macOS: brew install doctl"
        log "ERROR" "  Linux: snap install doctl"
        log "ERROR" "  Or download from: https://github.com/digitalocean/doctl/releases"
        exit 1
    fi
    
    # Check doctl authentication
    if ! doctl auth list &> /dev/null; then
        log "ERROR" "doctl is not authenticated. Please run: doctl auth init"
        exit 1
    fi
    
    # Check if Node.js is installed (for frontend build)
    if [ "$SKIP_BUILD" = false ] && ! command -v npm &> /dev/null; then
        log "ERROR" "npm is not installed. Please install Node.js first."
        exit 1
    fi
    
    # Check if deployment config exists
    if [ ! -f "$DEPLOYMENT_CONFIG" ]; then
        log "ERROR" "Deployment configuration not found at: $DEPLOYMENT_CONFIG"
        log "ERROR" "Please create .do/app.yaml first. See DEPLOYMENT_GUIDE.md for details."
        exit 1
    fi
    
    # Check if project structure is valid
    if [ ! -f "$PROJECT_ROOT/backend/main.py" ]; then
        log "ERROR" "Backend main.py not found. Please run from project root."
        exit 1
    fi
    
    if [ "$SKIP_BUILD" = false ] && [ ! -f "$PROJECT_ROOT/frontend/package.json" ]; then
        log "ERROR" "Frontend package.json not found. Use --skip-build if no frontend."
        exit 1
    fi
    
    log "SUCCESS" "Prerequisites check passed"
}

# Load and validate environment variables
validate_environment() {
    if [ "$SKIP_ENV_CHECK" = true ]; then
        log "INFO" "Skipping environment validation"
        return
    fi
    
    log "INFO" "Validating environment variables..."
    
    # Load .env file if it exists
    if [ -f "$ENV_FILE" ]; then
        log "DEBUG" "Loading environment from: $ENV_FILE"
        set -a
        source "$ENV_FILE"
        set +a
    fi
    
    # Required environment variables
    local required_vars=(
        "SUPABASE_URL"
        "SUPABASE_KEY" 
        "SUPABASE_SERVICE_KEY"
        "GOOGLE_API_KEY"
        "JWT_SECRET"
    )
    
    local missing_vars=()
    
    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            missing_vars+=("$var")
        fi
    done
    
    if [ ${#missing_vars[@]} -gt 0 ]; then
        log "ERROR" "Missing required environment variables:"
        for var in "${missing_vars[@]}"; do
            log "ERROR" "  - $var"
        done
        log "ERROR" "Please set these in your .env file or environment"
        log "ERROR" "See .env.example for template"
        exit 1
    fi
    
    # Validate format of key variables
    if [[ ! "$SUPABASE_URL" =~ ^https://.*\.supabase\.co$ ]]; then
        log "ERROR" "SUPABASE_URL must be in format: https://xxx.supabase.co"
        exit 1
    fi
    
    if [ ${#JWT_SECRET} -lt 32 ]; then
        log "WARN" "JWT_SECRET should be at least 32 characters for security"
    fi
    
    log "SUCCESS" "Environment validation passed"
}

# Build frontend
build_frontend() {
    if [ "$SKIP_BUILD" = true ]; then
        log "INFO" "Skipping frontend build"
        return
    fi
    
    log "INFO" "Building frontend application..."
    
    cd "$PROJECT_ROOT/frontend"
    
    # Check if node_modules exists
    if [ ! -d "node_modules" ]; then
        log "INFO" "Installing frontend dependencies..."
        show_progress "Installing dependencies" 3
        npm ci
    fi
    
    # Build the frontend
    log "INFO" "Building production frontend..."
    show_progress "Building frontend" 5
    npm run build
    
    # Verify build output
    if [ ! -f "dist/index.html" ]; then
        log "ERROR" "Frontend build failed - dist/index.html not found"
        exit 1
    fi
    
    local build_size=$(du -sh dist/ | cut -f1)
    log "SUCCESS" "Frontend build completed successfully (size: $build_size)"
    
    cd "$PROJECT_ROOT"
}

# Get app configuration
get_app_config() {
    if [ -n "$APP_NAME" ]; then
        echo "$APP_NAME"
        return
    fi
    
    # Extract app name from app.yaml
    local app_name=$(grep "^name:" "$DEPLOYMENT_CONFIG" | awk '{print $2}')
    if [ -z "$app_name" ]; then
        log "ERROR" "Could not determine app name from app.yaml"
        exit 1
    fi
    echo "$app_name"
}

# Check if app exists
app_exists() {
    local app_name="$1"
    doctl apps list --format Name --no-header | grep -q "^$app_name$"
}

# Get app ID
get_app_id() {
    local app_name="$1"
    doctl apps list --format ID,Name --no-header | grep "$app_name$" | awk '{print $1}'
}

# Update app.yaml with current configuration
update_app_config() {
    local temp_config="/tmp/app-deploy.yaml"
    cp "$DEPLOYMENT_CONFIG" "$temp_config"
    
    # Update environment if specified
    if [ -n "$ENVIRONMENT" ]; then
        log "DEBUG" "Setting environment to: $ENVIRONMENT"
        # Update environment variables in the config
        sed -i.bak "s/value: \"production\"/value: \"$ENVIRONMENT\"/g" "$temp_config"
        sed -i.bak "s/value: \"development\"/value: \"$ENVIRONMENT\"/g" "$temp_config"
    fi
    
    # Update domain if specified
    if [ -n "$DOMAIN" ]; then
        log "DEBUG" "Setting domain to: $DOMAIN"
        sed -i.bak "s/your-domain.com/$DOMAIN/g" "$temp_config"
    fi
    
    # Update GitHub repo if specified
    if [ -n "$GITHUB_REPO" ]; then
        log "DEBUG" "Setting GitHub repo to: $GITHUB_REPO"
        sed -i.bak "s/your-github-username\/ai-agent-platform/$GITHUB_REPO/g" "$temp_config"
    fi
    
    echo "$temp_config"
}

# Create new app
create_app() {
    local app_name="$1"
    local config_file="$2"
    
    log "INFO" "Creating new DigitalOcean app: $app_name"
    
    if [ "$DRY_RUN" = true ]; then
        log "INFO" "DRY RUN: Would create app with config: $config_file"
        return
    fi
    
    show_progress "Creating app" 5
    
    local app_id=$(doctl apps create --spec "$config_file" --format ID --no-header)
    
    if [ -z "$app_id" ]; then
        log "ERROR" "Failed to create app"
        exit 1
    fi
    
    log "SUCCESS" "App created successfully with ID: $app_id"
    
    # Wait for initial deployment
    wait_for_deployment "$app_id"
    
    return 0
}

# Update existing app
update_app() {
    local app_id="$1"
    local config_file="$2"
    
    log "INFO" "Updating DigitalOcean app: $app_id"
    
    if [ "$DRY_RUN" = true ]; then
        log "INFO" "DRY RUN: Would update app $app_id with config: $config_file"
        return
    fi
    
    show_progress "Updating app" 3
    
    doctl apps update "$app_id" --spec "$config_file"
    
    log "SUCCESS" "App update initiated"
    
    # Wait for deployment to complete
    wait_for_deployment "$app_id"
}

# Wait for deployment to complete
wait_for_deployment() {
    local app_id="$1"
    local max_wait=1200  # 20 minutes
    local wait_time=0
    local check_interval=30
    
    log "INFO" "Waiting for deployment to complete..."
    
    while [ $wait_time -lt $max_wait ]; do
        local deployment_status=$(doctl apps list-deployments "$app_id" --format Phase --no-header | head -1)
        
        case "$deployment_status" in
            "ACTIVE")
                log "SUCCESS" "Deployment completed successfully!"
                return 0
                ;;
            "ERROR"|"FAILED")
                log "ERROR" "Deployment failed!"
                show_deployment_logs "$app_id"
                exit 1
                ;;
            "PENDING"|"BUILDING"|"DEPLOYING")
                log "INFO" "Deployment in progress... (status: $deployment_status)"
                ;;
            *)
                log "WARN" "Unknown deployment status: $deployment_status"
                ;;
        esac
        
        sleep $check_interval
        wait_time=$((wait_time + check_interval))
        
        # Show progress
        local progress=$((wait_time * 100 / max_wait))
        echo -ne "\rProgress: $progress% ($wait_time/${max_wait}s)"
    done
    
    echo ""
    log "ERROR" "Deployment timeout after $max_wait seconds"
    exit 1
}

# Show deployment logs
show_deployment_logs() {
    local app_id="$1"
    local component="${2:-backend}"
    
    log "INFO" "Showing recent logs for component: $component"
    doctl apps logs "$app_id" --component "$component" --tail 50
}

# Get app status
get_app_status() {
    local app_name="$1"
    
    if ! app_exists "$app_name"; then
        log "ERROR" "App '$app_name' does not exist"
        return 1
    fi
    
    local app_id=$(get_app_id "$app_name")
    
    log "INFO" "App Status for: $app_name (ID: $app_id)"
    
    # Get app details
    doctl apps get "$app_id" --format Name,DefaultIngress,UpdatedAt,Phase
    
    # Get deployment status
    log "INFO" "Recent Deployments:"
    doctl apps list-deployments "$app_id" --format ID,Phase,CreatedAt | head -5
    
    # Test health endpoints
    local app_url=$(doctl apps get "$app_id" --format DefaultIngress --no-header)
    if [ -n "$app_url" ]; then
        log "INFO" "Testing health endpoints..."
        
        if curl -s --max-time 10 "https://$app_url/health" > /dev/null; then
            log "SUCCESS" "Backend health check: PASSED"
        else
            log "ERROR" "Backend health check: FAILED"
        fi
        
        if curl -s --max-time 10 "https://$app_url/" > /dev/null; then
            log "SUCCESS" "Frontend health check: PASSED"
        else
            log "WARN" "Frontend health check: FAILED (may be normal if not built)"
        fi
    fi
}

# Rollback deployment
rollback_deployment() {
    local app_name="$1"
    
    if ! app_exists "$app_name"; then
        log "ERROR" "App '$app_name' does not exist"
        return 1
    fi
    
    local app_id=$(get_app_id "$app_name")
    
    log "INFO" "Available deployments for rollback:"
    doctl apps list-deployments "$app_id" --format ID,Phase,CreatedAt | head -10
    
    echo -n "Enter deployment ID to rollback to: "
    read -r deployment_id
    
    if [ -z "$deployment_id" ]; then
        log "ERROR" "No deployment ID provided"
        return 1
    fi
    
    log "WARN" "This will rollback the app to deployment: $deployment_id"
    echo -n "Are you sure? (y/N): "
    read -r confirm
    
    if [[ "$confirm" =~ ^[Yy]$ ]]; then
        log "INFO" "Rolling back deployment..."
        # Note: DigitalOcean doesn't have direct rollback, so we'd need to redeploy
        log "ERROR" "Direct rollback not supported. Please redeploy with previous configuration."
        return 1
    else
        log "INFO" "Rollback cancelled"
    fi
}

# Destroy app
destroy_app() {
    local app_name="$1"
    
    if ! app_exists "$app_name"; then
        log "ERROR" "App '$app_name' does not exist"
        return 1
    fi
    
    local app_id=$(get_app_id "$app_name")
    
    log "WARN" "This will permanently destroy the app: $app_name (ID: $app_id)"
    log "WARN" "All data and configuration will be lost!"
    echo -n "Type 'DELETE' to confirm: "
    read -r confirm
    
    if [ "$confirm" = "DELETE" ]; then
        log "INFO" "Destroying app..."
        doctl apps delete "$app_id" --force
        log "SUCCESS" "App destroyed successfully"
    else
        log "INFO" "Destruction cancelled"
    fi
}

# Validate configuration
validate_config() {
    log "INFO" "Validating deployment configuration..."
    
    # Check app.yaml syntax
    if command -v yq &> /dev/null; then
        yq eval '.' "$DEPLOYMENT_CONFIG" > /dev/null
        log "SUCCESS" "app.yaml syntax is valid"
    else
        log "WARN" "yq not installed, skipping YAML validation"
    fi
    
    # Validate environment
    validate_environment
    
    # Check GitHub repo accessibility (if specified)
    if [ -n "$GITHUB_REPO" ]; then
        log "INFO" "Checking GitHub repository access..."
        if git ls-remote "https://github.com/$GITHUB_REPO.git" &> /dev/null; then
            log "SUCCESS" "GitHub repository is accessible"
        else
            log "ERROR" "GitHub repository is not accessible: $GITHUB_REPO"
            exit 1
        fi
    fi
    
    log "SUCCESS" "Configuration validation completed"
}

# Main deployment function
deploy_app() {
    local app_name=$(get_app_config)
    
    log "INFO" "Starting deployment for: $app_name"
    log "INFO" "Environment: ${ENVIRONMENT:-default}"
    log "INFO" "Domain: ${DOMAIN:-default}"
    
    # Update configuration
    local config_file=$(update_app_config)
    
    # Check if app exists
    if app_exists "$app_name"; then
        if [ "$FORCE_CREATE" = true ]; then
            log "WARN" "Force create requested - destroying existing app"
            destroy_app "$app_name"
            create_app "$app_name" "$config_file"
        else
            local app_id=$(get_app_id "$app_name")
            update_app "$app_id" "$config_file"
        fi
    else
        create_app "$app_name" "$config_file"
    fi
    
    # Show final status
    get_app_status "$app_name"
    
    # Cleanup temp config
    rm -f "$config_file"
    
    log "SUCCESS" "Deployment completed successfully!"
    log "INFO" "Log file saved to: $LOG_FILE"
}

# Main execution
main() {
    echo -e "${PURPLE}AI Agent Platform - DigitalOcean Deployment Script v1.0${NC}"
    echo "=================================================="
    
    parse_args "$@"
    
    log "INFO" "Starting deployment process..."
    log "INFO" "Command: $COMMAND"
    log "INFO" "Log file: $LOG_FILE"
    
    case "$COMMAND" in
        "deploy")
            check_prerequisites
            validate_environment
            build_frontend
            deploy_app
            ;;
        "create")
            FORCE_CREATE=true
            check_prerequisites
            validate_environment
            build_frontend
            deploy_app
            ;;
        "update")
            check_prerequisites
            validate_environment
            build_frontend
            local app_name=$(get_app_config)
            local app_id=$(get_app_id "$app_name")
            local config_file=$(update_app_config)
            update_app "$app_id" "$config_file"
            rm -f "$config_file"
            ;;
        "status")
            check_prerequisites
            local app_name=$(get_app_config)
            get_app_status "$app_name"
            ;;
        "logs")
            check_prerequisites
            local app_name=$(get_app_config)
            local app_id=$(get_app_id "$app_name")
            local component="${2:-backend}"
            show_deployment_logs "$app_id" "$component"
            ;;
        "rollback")
            check_prerequisites
            local app_name=$(get_app_config)
            rollback_deployment "$app_name"
            ;;
        "destroy")
            check_prerequisites
            local app_name=$(get_app_config)
            destroy_app "$app_name"
            ;;
        "validate")
            check_prerequisites
            validate_config
            ;;
        *)
            log "ERROR" "Unknown command: $COMMAND"
            show_usage
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@" 