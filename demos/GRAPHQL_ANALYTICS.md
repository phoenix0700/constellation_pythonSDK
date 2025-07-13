# 📊 GraphQL Analytics for Portfolio Tracker

A comprehensive GraphQL-powered analytics dashboard providing real-time insights into your Constellation Network portfolio with live mainnet data.

## 🚀 Features

### 📈 Real-Time Analytics
- **Live Portfolio Statistics**: Total balance, addresses, transactions, and performance metrics
- **Transaction Analytics**: Volume trends, transaction types, and activity patterns
- **Network Analytics**: Your share of the network, health scores, and growth metrics
- **Performance Metrics**: ROI tracking, volatility analysis, and portfolio performance

### 🔥 Interactive Visualizations
- **Area Charts**: Transaction volume trends over time
- **Pie Charts**: Balance distribution across addresses
- **Bar Charts**: Transaction type breakdown (incoming/outgoing/internal)
- **Radar Charts**: Multi-dimensional portfolio performance analysis
- **Progress Bars**: Network health and activity scores

### ⚡ Real-Time Data Streaming
- **WebSocket Subscriptions**: Live updates for portfolio changes
- **Transaction Feed**: Real-time transaction notifications
- **Network Pulse**: Live network activity monitoring
- **Auto-refresh**: Configurable polling intervals

### 🎯 Advanced Analytics
- **Portfolio Performance Radar**: Multi-dimensional analysis of ROI, growth, stability, activity, and diversification
- **Risk Assessment**: Portfolio concentration risk and volatility scoring
- **Token Distribution**: Metagraph token holdings and diversification metrics
- **Network Comparison**: Your portfolio's position within the broader network

## 🛠 Architecture

### Backend (GraphQL Server)
- **Strawberry GraphQL**: Modern Python GraphQL server
- **FastAPI Integration**: RESTful and GraphQL endpoints
- **Real-time Subscriptions**: WebSocket-based live data streaming
- **Live Mainnet Data**: Direct integration with Constellation Network

### Frontend (Apollo Client)
- **Apollo Client**: Full-featured GraphQL client with caching
- **Real-time Subscriptions**: WebSocket connections for live updates
- **Recharts**: Beautiful, responsive chart library
- **Ant Design**: Professional UI components

## 📦 Installation

### Quick Setup
```bash
# Run the automated setup script
./setup-graphql-analytics.sh
```

### Manual Installation

#### Backend Dependencies
```bash
cd backend
pip install strawberry-graphql[fastapi] uvicorn[standard] websockets graphql-core
```

#### Frontend Dependencies
```bash
cd frontend
npm install @apollo/client graphql graphql-ws recharts
```

## 🚀 Usage

### 1. Start the Backend Server
```bash
cd backend
python app.py
```

The GraphQL server will be available at:
- **GraphQL Endpoint**: `http://localhost:8000/graphql`
- **GraphQL Playground**: `http://localhost:8000/graphql` (in browser)

### 2. Start the Frontend
```bash
cd frontend
npm start
```

### 3. Access Analytics
Navigate to: `http://localhost:3000/analytics`

## 🔍 GraphQL Schema

### Core Types
```graphql
type PortfolioStats {
  totalBalance: Float!
  totalAddresses: Int!
  totalTransactions: Int!
  averageBalance: Float!
  largestBalance: Float!
  smallestBalance: Float!
  balanceDistribution: [Float!]!
  lastUpdated: String!
}

type TransactionAnalytics {
  totalVolume: Float!
  transactionCount: Int!
  averageAmount: Float!
  peakHour: Int!
  peakDay: String!
  incomingCount: Int!
  outgoingCount: Int!
  internalCount: Int!
  volumeTrend: [Float!]!
  countTrend: [Int!]!
}

type NetworkAnalytics {
  totalNetworkBalance: Float!
  totalNetworkTransactions: Int!
  networkGrowthRate: Float!
  yourNetworkShare: Float!
  networkActivityScore: Float!
  recentNetworkTransactions: [String!]!
  networkHealthScore: Float!
}
```

### Queries
```graphql
query GetAnalyticsDashboard {
  portfolioStats { ... }
  transactionAnalytics(days: 30) { ... }
  networkAnalytics { ... }
  performanceMetrics { ... }
  tokenDistribution { ... }
}
```

### Subscriptions
```graphql
subscription PortfolioUpdates {
  portfolioUpdates {
    timestamp
    updateType
    data
  }
}
```

## 📊 Analytics Features

### Portfolio Performance Radar
Multi-dimensional analysis covering:
- **ROI**: Return on investment tracking
- **Growth**: Portfolio growth trends
- **Stability**: Volatility and risk assessment
- **Activity**: Transaction frequency and engagement
- **Diversification**: Address and token distribution

### Real-Time Data Streams
- **Portfolio Updates**: Balance changes, new transactions
- **Transaction Feed**: Live transaction notifications
- **Network Pulse**: Network-wide activity and health metrics

### Network Analytics
- **Network Share**: Your portfolio's percentage of total network
- **Health Score**: Network stability and performance indicators
- **Activity Score**: Network engagement and transaction volume
- **Growth Rate**: Network expansion and adoption metrics

## 🎨 Customization

### Chart Colors
```typescript
const CHART_COLORS = {
  primary: '#667eea',
  secondary: '#764ba2',
  success: '#52c41a',
  warning: '#faad14',
  error: '#f5222d',
  info: '#1890ff',
  gradient: ['#667eea', '#764ba2', '#f093fb', '#f5576c', '#4facfe', '#00f2fe']
};
```

### Styling
The analytics page uses styled-components with:
- **Glassmorphism Effect**: Backdrop blur and transparency
- **Gradient Backgrounds**: Beautiful color transitions
- **Card Animations**: Hover effects and transitions
- **Responsive Design**: Mobile-friendly layouts

## 🔧 Configuration

### Environment Variables
```bash
# Frontend (.env)
REACT_APP_API_URL=http://localhost:8000
REACT_APP_GRAPHQL_URL=http://localhost:8000/graphql
REACT_APP_GRAPHQL_WS_URL=ws://localhost:8000/graphql
```

### GraphQL Client Configuration
```typescript
const apolloClient = new ApolloClient({
  link: splitLink, // HTTP + WebSocket
  cache: new InMemoryCache(),
  defaultOptions: {
    watchQuery: { errorPolicy: 'all' },
    query: { errorPolicy: 'all' }
  }
});
```

## 📈 Performance Features

### Caching Strategy
- **Apollo Client Cache**: Intelligent query result caching
- **Polling Intervals**: Configurable refresh rates
- **Subscription Management**: Efficient WebSocket connections

### Data Optimization
- **Batch Operations**: Multiple queries in single requests
- **Selective Fetching**: Only request needed data fields
- **Error Boundaries**: Graceful error handling

## 🧪 Demo Mode

The analytics system includes a comprehensive demo mode that works even without live data:
- **Mock Data**: Realistic portfolio statistics and trends
- **Interactive Charts**: All visualizations work with demo data
- **Real-time Simulation**: Simulated live updates and streaming
- **Full Feature Demo**: Complete analytics experience

## 🔍 Troubleshooting

### Common Issues

1. **GraphQL Server Not Starting**
   ```bash
   # Check if strawberry-graphql is installed
   pip list | grep strawberry
   
   # Reinstall if needed
   pip install strawberry-graphql[fastapi]
   ```

2. **Frontend Build Errors**
   ```bash
   # Clear cache and reinstall
   npm run build
   rm -rf node_modules package-lock.json
   npm install
   ```

3. **WebSocket Connection Issues**
   ```bash
   # Check if websockets is installed
   pip list | grep websockets
   
   # Install if needed
   pip install websockets
   ```

### Debug Mode
Enable debug logging in the GraphQL server:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 🚀 Production Deployment

### Backend Deployment
```bash
# Use production WSGI server
pip install gunicorn
gunicorn app:app -w 4 -k uvicorn.workers.UvicornWorker
```

### Frontend Deployment
```bash
# Build for production
npm run build

# Serve static files
npx serve -s build
```

## 📝 API Documentation

The GraphQL API is self-documenting. Access the GraphQL Playground at `http://localhost:8000/graphql` to explore:
- **Schema Browser**: Complete type definitions
- **Query Builder**: Interactive query construction
- **Subscription Tester**: Real-time subscription testing

## 🎯 Future Enhancements

- **Advanced Charting**: More chart types and customization
- **Alert System**: Portfolio alerts and notifications
- **Historical Analysis**: Long-term trend analysis
- **Export Features**: Data export and reporting
- **Mobile App**: React Native mobile version

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Implement your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

This project is part of the Constellation SDK and follows the same license terms.

---

**🍓 Powered by Strawberry GraphQL & Apollo Client**  
**🔥 Real-time Analytics with Live Mainnet Data**  
**📊 Beautiful Visualizations with Recharts**