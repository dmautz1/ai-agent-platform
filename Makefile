# =============================================================================
# AI Agent Platform - Configuration Management
# =============================================================================

.PHONY: help config-dev config-prod config-check setup-dev deploy clean project-status deploy-status deploy-logs

# Default target
help:
	@echo "🔧 AI Agent Platform Configuration Management"
	@echo ""
	@echo "Available commands:"
	@echo "  setup-dev     - Install dependencies and generate development config"
	@echo "  config-dev    - Generate development environment files"
	@echo "  config-prod   - Generate production environment files"
	@echo "  config-check  - Validate configuration without generating files"
	@echo "  deploy        - Deploy to production (generates prod config first)"
	@echo "  deploy-status - Check deployment status"
	@echo "  deploy-logs   - Show deployment logs"
	@echo "  project-status- Show DigitalOcean project status"
	@echo "  clean         - Remove generated environment files"
	@echo ""
	@echo "Configuration is managed from config.yaml"
	@echo "Generated files: .env, backend/.env, frontend/.env.local, .do/app.yaml"

# Install dependencies and generate development config
setup-dev:
	@echo "🚀 Setting up development environment..."
	pip install -r requirements.txt
	@echo "📝 Generating development configuration..."
	python scripts/generate_config.py development
	@echo "✅ Development setup complete!"

# Generate development environment files
config-dev:
	@echo "📝 Generating development configuration..."
	python scripts/generate_config.py development

# Generate production environment files  
config-prod:
	@echo "📝 Generating production configuration..."
	python scripts/generate_config.py production

# Validate configuration without generating files
config-check:
	@echo "🔍 Validating configuration..."
	python scripts/generate_config.py development --dry-run
	@echo "✅ Configuration validation complete!"

# Deploy to production (generates prod config first)
deploy: config-prod
	@echo "🚀 Deploying to production..."
	./scripts/deploy.sh

# Remove generated environment files
clean:
	@echo "🧹 Cleaning generated configuration files..."
	rm -f .env
	rm -f backend/.env
	rm -f frontend/.env.local
	@echo "✅ Cleanup complete!"

# Show current configuration status
status:
	@echo "📊 Configuration Status"
	@echo ""
	@echo "Generated files:"
	@if [ -f ".env" ]; then echo "  ✅ .env"; else echo "  ❌ .env"; fi
	@if [ -f "backend/.env" ]; then echo "  ✅ backend/.env"; else echo "  ❌ backend/.env"; fi
	@if [ -f "frontend/.env.local" ]; then echo "  ✅ frontend/.env.local"; else echo "  ❌ frontend/.env.local"; fi
	@if [ -f ".do/app.yaml" ]; then echo "  ✅ .do/app.yaml"; else echo "  ❌ .do/app.yaml"; fi
	@echo ""
	@echo "Source configuration: config.yaml"

# Check deployment status
deploy-status:
	@echo "🔍 Checking deployment status..."
	./scripts/deploy.sh status

# Show deployment logs
deploy-logs:
	@echo "📄 Showing deployment logs..."
	./scripts/deploy.sh logs

# Show DigitalOcean project status
project-status:
	@echo "📊 DigitalOcean Project Status"
	@echo ""
	@if command -v doctl >/dev/null 2>&1; then \
		echo "Projects:"; \
		doctl projects list --format Name,Description,Environment,UpdatedAt | head -10; \
		echo ""; \
		echo "Apps:"; \
		doctl apps list | head -10; \
	else \
		echo "❌ doctl CLI not installed"; \
	fi 