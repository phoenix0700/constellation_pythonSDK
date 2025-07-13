# 🏦 DeFi Portfolio Tracker Demo

A comprehensive portfolio tracking application for Constellation Network, showcasing the Python SDK's capabilities for multi-address DAG and metagraph token monitoring.

## 🎯 Overview

This demo application demonstrates how to build a real-world DeFi portfolio tracker using the Constellation Python SDK. It tracks balances, transactions, and performance across multiple DAG addresses and metagraph tokens without requiring a custom metagraph.

## ✨ Features

### 📊 Portfolio Management
- **Multi-address tracking** - Monitor multiple DAG addresses with custom labels
- **Auto-discovery** - Automatically discover and track metagraph tokens
- **Real-time updates** - Live balance updates using SDK streaming capabilities
- **Transaction history** - Track portfolio changes over time
- **Performance analytics** - ROI calculations, allocation percentages, profit/loss

### 🔍 Advanced Analytics
- **Portfolio composition** - Visual breakdown of DAG vs metagraph tokens
- **Historical performance** - Track portfolio value over time
- **Transaction analysis** - Categorize and analyze transaction patterns
- **Yield tracking** - Monitor rewards and staking returns
- **Risk assessment** - Portfolio diversity and concentration analysis

### 🌐 Network Integration
- **Multi-network support** - MainNet, TestNet, IntegrationNet
- **Efficient queries** - GraphQL for complex data fetching
- **Batch operations** - Optimized REST calls for multiple addresses
- **Caching** - Smart caching for improved performance

## 🏗️ Architecture

```
Portfolio Tracker
├── Backend (Python SDK)
│   ├── Portfolio Service - Core portfolio management
│   ├── Discovery Service - Metagraph and token discovery
│   ├── Analytics Service - Performance calculations
│   └── Streaming Service - Real-time updates
├── Frontend (React/Vue)
│   ├── Dashboard - Portfolio overview
│   ├── Analytics - Performance charts
│   ├── Transactions - Transaction history
│   └── Settings - Address management
└── Data Layer
    ├── SDK Network Queries - Live network data
    ├── Local Cache - Performance optimization
    └── Configuration - User preferences
```

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- Constellation Python SDK
- Node.js 16+ (for frontend)
- Web browser

### Installation
```bash
# Clone the repository
git clone https://github.com/constellation-labs/constellation-python-sdk.git
cd constellation-python-sdk/demos/portfolio_tracker

# Install backend dependencies
pip install -r requirements.txt

# Install frontend dependencies
cd frontend
npm install
```

### Running the Demo
```bash
# Start the backend server
python backend/app.py

# Start the frontend (new terminal)
cd frontend
npm start

# Open browser to http://localhost:3000
```

## 📱 Usage Examples

### Adding Addresses
```python
from portfolio_tracker import PortfolioTracker

# Initialize portfolio tracker
tracker = PortfolioTracker(network='mainnet')

# Add addresses to track
tracker.add_address('DAG123...', label='Main Wallet')
tracker.add_address('DAG456...', label='Trading Wallet')
tracker.add_address('DAG789...', label='DeFi Vault')

# Get portfolio summary
portfolio = tracker.get_portfolio_summary()
print(f"Total Value: {portfolio['total_value']:.2f} DAG")
```

### Real-time Monitoring
```python
# Enable real-time updates
tracker.enable_streaming()

# Set up balance change alerts
tracker.on_balance_change(lambda addr, change: 
    print(f"Balance change: {addr} changed by {change:.8f} DAG")
)

# Monitor for 10 minutes
tracker.monitor(duration=600)
```

### Analytics Dashboard
```python
# Get performance metrics
performance = tracker.get_performance_metrics()

print(f"24h Change: {performance['change_24h']:.2f}%")
print(f"7d Change: {performance['change_7d']:.2f}%")
print(f"Portfolio ROI: {performance['roi']:.2f}%")
```

## 🎯 SDK Features Demonstrated

### Core Features
- ✅ **Multi-address balance queries** - Efficient batch operations
- ✅ **Transaction history** - Comprehensive transaction tracking
- ✅ **Metagraph discovery** - Auto-discover available tokens
- ✅ **Network switching** - Support for multiple networks

### Advanced Features
- ✅ **GraphQL queries** - Complex data relationships
- ✅ **Real-time streaming** - Live balance and transaction updates
- ✅ **Batch operations** - Optimized multi-address queries
- ✅ **Async support** - High-performance concurrent operations
- ✅ **Caching** - Smart caching for improved performance
- ✅ **Error handling** - Robust error recovery

### Performance Features
- ✅ **Connection pooling** - Efficient network connections
- ✅ **Rate limiting** - Respect API limits
- ✅ **Retry logic** - Automatic retry on failures
- ✅ **Timeout handling** - Graceful timeout management

## 📊 Technical Implementation

### Backend Services
- **`PortfolioService`** - Core portfolio management and calculations
- **`DiscoveryService`** - Metagraph and token discovery
- **`AnalyticsService`** - Performance metrics and analytics
- **`StreamingService`** - Real-time updates and notifications

### Frontend Components
- **Dashboard** - Portfolio overview with charts and summaries
- **Analytics** - Detailed performance analysis and trends
- **Transactions** - Transaction history with filtering and search
- **Settings** - Address management and preferences

### Data Flow
1. **Address Management** - User adds DAG addresses to track
2. **Discovery** - Auto-discover metagraph tokens for each address
3. **Data Fetching** - Use GraphQL and REST APIs to fetch portfolio data
4. **Analytics** - Calculate performance metrics and trends
5. **Real-time Updates** - Stream live balance and transaction changes
6. **Visualization** - Display data in intuitive charts and tables

## 🔧 Configuration

### Network Configuration
```python
# Configure for different networks
PORTFOLIO_CONFIG = {
    'network': 'mainnet',  # or 'testnet', 'integrationnet'
    'cache_ttl': 300,      # Cache TTL in seconds
    'update_interval': 60,  # Update interval in seconds
    'max_addresses': 50,   # Maximum addresses to track
    'batch_size': 10,      # Batch size for queries
}
```

### Feature Flags
```python
FEATURES = {
    'real_time_updates': True,
    'advanced_analytics': True,
    'transaction_categorization': True,
    'yield_tracking': True,
    'alert_system': True,
}
```

## 🎨 Screenshots

*(Screenshots will be added once the frontend is built)*

- Dashboard Overview
- Portfolio Analytics
- Transaction History
- Address Management
- Real-time Updates

## 🛠️ Development

### Project Structure
```
portfolio_tracker/
├── backend/
│   ├── app.py              # Flask/FastAPI server
│   ├── services/
│   │   ├── portfolio.py    # Portfolio management
│   │   ├── discovery.py    # Token discovery
│   │   ├── analytics.py    # Performance analytics
│   │   └── streaming.py    # Real-time updates
│   ├── models/
│   │   ├── portfolio.py    # Portfolio data models
│   │   └── analytics.py    # Analytics models
│   └── utils/
│       ├── cache.py        # Caching utilities
│       └── config.py       # Configuration
├── frontend/
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── pages/          # Application pages
│   │   ├── services/       # API services
│   │   └── utils/          # Utilities
│   └── public/             # Static assets
└── tests/
    ├── backend/            # Backend tests
    └── frontend/           # Frontend tests
```

### Running Tests
```bash
# Backend tests
python -m pytest tests/backend/

# Frontend tests
cd frontend
npm test
```

## 🎯 Future Enhancements

### Phase 2 Features
- **Social features** - Portfolio sharing and comparison
- **Advanced alerts** - Price and balance notifications
- **DeFi integrations** - Yield farming and staking data
- **Mobile app** - React Native mobile version
- **Export functionality** - PDF reports and CSV exports

### Integration Options
- **Custom metagraph** - Store user preferences and social data
- **Push notifications** - Real-time alerts via push notifications
- **API endpoints** - Public API for third-party integrations
- **Webhook support** - Integration with external systems

## 📚 Learning Resources

### SDK Documentation
- [Constellation Python SDK Documentation](../README.md)
- [GraphQL Usage Guide](../docs/graphql.md)
- [Streaming Guide](../docs/streaming.md)
- [Performance Optimization](../docs/performance.md)

### Related Examples
- [GraphQL Real-World Use Cases](../examples/graphql_real_world_use_cases.py)
- [Trading Bot Integration](../examples/trading_bot_graphql.py)
- [Real-time Streaming Demo](../examples/real_time_streaming_demo.py)

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](../CONTRIBUTING.md) for details.

### Development Setup
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](../LICENSE) file for details.

## 🎉 Acknowledgments

- Built with [Constellation Python SDK](https://github.com/constellation-labs/constellation-python-sdk)
- Powered by [Constellation Network](https://constellationnetwork.io)
- Inspired by the DeFi community

---

**Ready to build your own DeFi applications?** This demo shows you how! 🚀