# Stepstone Job Search MCP Server

A Model Context Protocol (MCP) server for searching job listings on Stepstone.de. This server transforms job search functionality into a tool that can be used with MCP-compatible clients like Smithery, Claude Desktop, and other AI assistants.

[![smithery badge](https://smithery.ai/badge/@kdkiss/mcp-stepstone)](https://smithery.ai/server/@kdkiss/mcp-stepstone)

## 🎯 Overview

**`mcp-stepstone`** is an MCP-compatible CLI module that fetches job listings from [Stepstone.de](https://www.stepstone.de) based on dynamic keywords and location parameters. It provides a standardized interface for AI assistants to access real-time job market data from Germany's largest job portal.

## ✨ Features

- 🔍 **Multi-term Search**: Search job listings using multiple keywords simultaneously
- 📍 **Location-based Search**: German postal code targeting with configurable radius
- 🎯 **Smart Filtering**: Duplicate job detection and removal
- 🛡️ **Robust Error Handling**: Comprehensive logging and graceful failure recovery
- 📊 **Structured Data**: Clean JSON output with job title, company, location, and direct links
- 🔄 **Real-time Data**: Live scraping of Stepstone.de for current job postings
- 🏗️ **MCP Compliant**: Full Model Context Protocol implementation
- 🐳 **Docker Ready**: Containerized deployment support
- 🔧 **Configurable**: Environment-based configuration for production use

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- pip package manager
- Internet connection for Stepstone.de access

### Installation Options

#### Option 1: Smithery (Recommended)
```bash
npx -y @smithery/cli install @kdkiss/mcp-stepstone --client claude
```

#### Option 2: Manual Installation
```bash
# Clone or download the repository
git clone <repository-url>
cd mcp-stepstone

# Install dependencies
pip install -r requirements.txt

# Make executable (Unix systems)
chmod +x stepstone_server.py
```

#### Option 3: Docker
```bash
# Build the container
docker build -t mcp-stepstone .

# Run the container
docker run -it mcp-stepstone
```

## 🔧 Configuration

### MCP Client Configuration

#### Smithery Configuration
Add to your `mcp.json`:
```json
{
  "mcpServers": {
    "stepstone-job-search": {
      "command": "python",
      "args": ["/path/to/stepstone_server.py"],
      "description": "Search for job listings on Stepstone.de",
      "env": {
        "LOG_LEVEL": "INFO",
        "REQUEST_TIMEOUT": "10"
      }
    }
  }
}
```

#### Claude Desktop Configuration

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "stepstone-job-search": {
      "command": "python",
      "args": ["/absolute/path/to/stepstone_server.py"],
      "env": {
        "LOG_LEVEL": "DEBUG",
        "USER_AGENT": "MCP-Stepstone-Bot/1.0"
      }
    }
  }
}
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `LOG_LEVEL` | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `REQUEST_TIMEOUT` | `10` | HTTP request timeout in seconds |
| `USER_AGENT` | `Mozilla/5.0...` | Custom User-Agent string |
| `MAX_RETRIES` | `3` | Maximum retry attempts for failed requests |
| `CACHE_TTL` | `300` | Cache TTL in seconds (future feature) |

## 📖 Usage

### Available Tools

#### `search_jobs`
Search for job listings using multiple search terms with location-based filtering.

**Parameters:**
- `search_terms` (array, optional): List of job search terms
  - Default: `["fraud", "betrug", "compliance"]`
  - Example: `["data scientist", "machine learning", "python developer"]`
- `zip_code` (string, optional): German 5-digit postal code
  - Default: `"40210"` (Düsseldorf)
  - Example: `"10115"` (Berlin), `"80331"` (Munich)
- `radius` (integer, optional): Search radius in kilometers
  - Default: `5`
  - Range: 1-100 km

### Example Usage

#### Basic Search
```json
{
  "tool": "search_jobs",
  "parameters": {
    "search_terms": ["software engineer", "developer"]
  }
}
```

#### Location-Specific Search
```json
{
  "tool": "search_jobs",
  "parameters": {
    "search_terms": ["marketing manager", "digital marketing"],
    "zip_code": "10115",
    "radius": 15
  }
}
```

#### Specialized Search
```json
{
  "tool": "search_jobs",
  "parameters": {
    "search_terms": ["fraud analyst", "compliance officer", "risk management"],
    "zip_code": "60329",
    "radius": 25
  }
}
```

### Sample Output
```
Job Search Summary:
Search Terms: fraud analyst, compliance officer
Location: 60329 (±25km)
Total Jobs Found: 23

--- Results for 'fraud analyst' ---

1. Senior Fraud Analyst - Digital Banking
   Company: Deutsche Bank AG
   Location: Frankfurt am Main
   Description: Join our fraud prevention team to analyze transaction patterns...
   Link: https://www.stepstone.de/stellenangebote--Senior-Fraud-Analyst-Frankfurt-Deutsche-Bank-AG--1234567

2. Fraud Detection Specialist (m/w/d)
   Company: Commerzbank AG
   Location: Frankfurt am Main
   Description: Responsible for real-time fraud monitoring and investigation...
   Link: https://www.stepstone.de/stellenangebote--Fraud-Detection-Specialist-Frankfurt-Commerzbank--1234568
```

## 🏗️ Technical Architecture

### System Design
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   MCP Client    │────│  MCP Stepstone   │────│   Stepstone.de  │
│ (Claude/Smithery) │    │     Server       │    │   (Job Portal)  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                       ┌──────────────────┐
                       │  Job Scraper     │
                       │  - URL Builder   │
                       │  - HTML Parser   │
                       │  - Data Cleaner  │
                       └──────────────────┘
```

### Data Flow
1. **Request**: MCP client sends search request with parameters
2. **Validation**: Server validates input parameters
3. **URL Construction**: Builds Stepstone.de search URLs
4. **Web Scraping**: Fetches and parses job listings
5. **Data Processing**: Extracts and structures job information
6. **Response**: Returns formatted results to MCP client

### Key Components

#### StepstoneJobScraper ([`stepstone_server.py:35`](stepstone_server.py:35))
- **Purpose**: Handles all web scraping operations
- **Methods**:
  - `build_search_url()`: Constructs search URLs with parameters
  - `fetch_job_listings()`: Scrapes job data from Stepstone
  - `search_jobs()`: Orchestrates multi-term searches

#### MCP Server ([`stepstone_server.py:119`](stepstone_server.py:119))
- **Purpose**: MCP protocol implementation
- **Features**:
  - Tool registration (`search_jobs`)
  - Resource management (`stepstone://search-help`)
  - Error handling and validation
  - Logging and monitoring

## 🔒 Security & Best Practices

### Rate Limiting
- Built-in delays between requests
- Respectful User-Agent headers
- Configurable request timeouts
- Automatic retry with exponential backoff

### Data Privacy
- No personal data storage
- Temporary in-memory processing only
- No cookies or session persistence
- GDPR-compliant data handling

### Anti-Detection Measures
- Rotating User-Agent strings
- Random delays between requests
- Conservative request frequency
- Error handling for blocked requests

## ⚡ Performance Optimization

### Caching Strategy (Future Enhancement)
- Redis-based caching for frequent searches
- TTL-based cache expiration
- Cache invalidation on demand
- Memory usage optimization

### Scaling Considerations
- Stateless design for horizontal scaling
- Container-ready deployment
- Load balancer compatibility
- Health check endpoints

## 🧪 Development & Testing

### Local Development Setup
```bash
# Clone repository
git clone <repository-url>
cd mcp-stepstone

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install pytest pytest-asyncio black flake8

# Run tests
pytest tests/

# Format code
black stepstone_server.py

# Lint code
flake8 stepstone_server.py
```

### Testing the Server
```bash
# Test basic functionality
python stepstone_server.py

# Test with debug logging
LOG_LEVEL=DEBUG python stepstone_server.py

# Test specific search
echo '{"search_terms": ["test"], "zip_code": "40210"}' | python stepstone_server.py
```

### Debug Mode
```bash
# Run debug server
python debug_server.py

# Health check
python health.py
```

## 📊 Monitoring & Logging

### Log Levels
- **DEBUG**: Detailed request/response information
- **INFO**: General operation status
- **WARNING**: Non-critical issues
- **ERROR**: Critical failures and exceptions

### Health Checks
```bash
# Check server health
curl -X POST http://localhost:8080/health

# Expected response
{"status": "healthy", "timestamp": "2024-01-01T12:00:00Z"}
```

## 🌍 German Postal Code Reference

| City | Postal Code | Area | Region |
|------|-------------|------|---------|
| Berlin | 10115 | Mitte | Berlin |
| Munich | 80331 | City Center | Bavaria |
| Hamburg | 20095 | City Center | Hamburg |
| Cologne | 50667 | City Center | North Rhine-Westphalia |
| Frankfurt | 60329 | City Center | Hesse |
| Düsseldorf | 40210 | City Center | North Rhine-Westphalia |
| Stuttgart | 70173 | City Center | Baden-Württemberg |
| Leipzig | 04109 | City Center | Saxony |
| Dresden | 01067 | City Center | Saxony |
| Hanover | 30159 | City Center | Lower Saxony |

## 🔧 Troubleshooting

### Common Issues

#### Server Not Starting
```bash
# Check Python version
python --version  # Should be 3.8+

# Verify dependencies
pip list | grep -E "(requests|beautifulsoup4|mcp|lxml)"

# Check file permissions
ls -la stepstone_server.py
```

#### No Jobs Found
- **Invalid postal code**: Ensure 5-digit German postal code
- **Too narrow search**: Increase radius or use broader terms
- **Network issues**: Check internet connectivity
- **Stepstone changes**: Verify website structure hasn't changed

#### Import Errors
```bash
# Install missing dependencies
pip install -r requirements.txt

# Upgrade pip if needed
pip install --upgrade pip
```

#### Permission Errors (Unix)
```bash
# Make script executable
chmod +x stepstone_server.py

# Or run with python explicitly
python stepstone_server.py
```

### Debug Mode
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
python stepstone_server.py

# Check logs for detailed information
tail -f /var/log/stepstone-mcp.log
```

## 🤝 Contributing

### Development Workflow
1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Make changes and add tests
4. Run tests: `pytest tests/`
5. Format code: `black stepstone_server.py`
6. Commit changes: `git commit -m 'Add amazing feature'`
7. Push to branch: `git push origin feature/amazing-feature`
8. Create Pull Request

### Code Style
- Follow PEP 8 guidelines
- Use type hints where appropriate
- Add docstrings for all functions
- Include error handling for all external calls

### Testing Guidelines
- Write unit tests for all new functions
- Include integration tests for MCP endpoints
- Test edge cases and error conditions
- Ensure 80%+ code coverage

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🆘 Support

### Getting Help
- 📖 Check this README for common issues
- 🔍 Review logs for error messages
- 🐛 Report bugs via GitHub Issues
- 💬 Join our Discord community for discussions

### Resources
- [MCP Specification](https://github.com/modelcontextprotocol/specification)
- [Smithery Documentation](https://smithery.ai/docs)
- [Stepstone.de](https://www.stepstone.de) - Job portal
- [Python MCP SDK](https://github.com/modelcontextprotocol/python-sdk)

## 📈 Version History

### v1.1.0 (Current)
- Enhanced documentation and examples
- Added Docker support
- Improved error handling
- Added environment variable configuration
- Enhanced security features

### v1.0.0
- Initial release
- Basic job search functionality
- MCP protocol compliance
- German postal code support
- Comprehensive error handling

---

**Made with ❤️ for the German job market**
