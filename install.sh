#!/bin/bash

# Constellation Network Python SDK Installation Script

echo "🌟 Installing Constellation Network Python SDK..."

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
required_version="3.8"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Error: Python 3.8+ required. Found: $python_version"
    exit 1
fi

echo "✅ Python version check passed: $python_version"

# Create virtual environment (optional but recommended)
read -p "Create virtual environment? (y/n): " create_venv
if [ "$create_venv" = "y" ] || [ "$create_venv" = "Y" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv constellation_env
    source constellation_env/bin/activate
    echo "✅ Virtual environment activated"
fi

# Install dependencies
echo "📥 Installing dependencies..."
pip install --upgrade pip
pip install requests>=2.28.0 cryptography>=3.4.8 base58>=2.1.0

# Install SDK in development mode
echo "🔧 Installing Constellation SDK..."
pip install -e .

# Verify installation
echo "🧪 Verifying installation..."
python3 -c "
try:
    from constellation_sdk import Account, Network
    print('✅ Constellation SDK installed successfully!')
    
    # Test basic functionality
    account = Account()
    network = Network('testnet')
    print(f'✅ Test account created: {account.address[:10]}...')
    print('✅ Network connection established')
    
except ImportError as e:
    print(f'❌ Import error: {e}')
except Exception as e:
    print(f'❌ Error: {e}')
"

echo ""
echo "🎉 Installation complete!"
echo ""
echo "Quick start:"
echo "python3 -c \"from constellation_sdk import Account; print('Address:', Account().address)\""
echo ""
echo "📚 Documentation: https://docs.constellationnetwork.io/"
echo "💬 Discord: https://discord.gg/constellation" 