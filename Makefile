# Makefile for Constellation Network Python SDK

.PHONY: install test clean dev-install docs lint format

# Default Python command
PYTHON := python3
PIP := pip

# Installation
install:
	@echo "🌟 Installing Constellation Network Python SDK..."
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	$(PIP) install -e .
	@echo "✅ Installation complete!"

# Development installation with extra tools
dev-install: install
	@echo "🔧 Installing development dependencies..."
	$(PIP) install pytest pytest-cov black flake8 mypy
	@echo "✅ Development environment ready!"

# Run tests
test:
	@echo "🧪 Running unit tests..."
	$(PYTHON) -m pytest tests/ -v

# Test with coverage
test-coverage:
	@echo "🧪 Running tests with coverage..."
	$(PYTHON) -m pytest tests/ --cov=constellation_sdk --cov-report=html

# Lint code
lint:
	@echo "🔍 Linting code..."
	flake8 constellation_sdk/ tests/ examples/
	mypy constellation_sdk/

# Format code
format:
	@echo "🎨 Formatting code..."
	black constellation_sdk/ tests/ examples/

# Clean build artifacts
clean:
	@echo "🧹 Cleaning build artifacts..."
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf htmlcov/
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete

# Create virtual environment
venv:
	@echo "📦 Creating virtual environment..."
	$(PYTHON) -m venv constellation_env
	@echo "✅ Virtual environment created!"
	@echo "💡 Activate with: source constellation_env/bin/activate"

# Quick start example
demo:
	@echo "🚀 Running quick demo..."
	$(PYTHON) -c "from constellation_sdk import Account, Network; acc = Account(); print(f'Demo Account: {acc.address}'); net = Network('testnet'); print('Connected to TestNet')"

# Show help
help:
	@echo "Constellation Network Python SDK - Make Commands"
	@echo ""
	@echo "Installation:"
	@echo "  install       Install the SDK and dependencies"
	@echo "  dev-install   Install with development tools"
	@echo "  venv          Create virtual environment"
	@echo ""
	@echo "Testing:"
	@echo "  test          Run all tests"
	@echo "  test-coverage Run tests with coverage report"
	@echo ""
	@echo "Development:"
	@echo "  lint          Lint code with flake8 and mypy"
	@echo "  format        Format code with black"
	@echo "  clean         Clean build artifacts"
	@echo ""
	@echo "Examples:"
	@echo "  demo          Run quick demo"
	@echo ""
	@echo "Help:"
	@echo "  help          Show this help message" 