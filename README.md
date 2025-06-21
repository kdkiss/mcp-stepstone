# Stepstone Job Search MCP Server

A Model Context Protocol (MCP) server for searching job listings on Stepstone.de. This server transforms job search functionality into a tool that can be used with MCP-compatible clients like Smithery, Claude Desktop, and other AI assistants.

## Features

- 🔍 Search job listings on Stepstone.de using multiple search terms
- 📍 Location-based search with German postal codes
- 🎯 Configurable search radius
- 🛡️ Robust error handling and logging
- 📊 Structured job data extraction (title, company, location, link)
- 🔄 Duplicate job filtering
- 📚 Built-in help documentation

## Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Step 1: Install Dependencies

```bash
pip install requests beautifulsoup4 mcp lxml
```

Or using the requirements file:

```bash
pip install -r requirements.txt
```

### Step 2: Download the Server

Save the `stepstone_server.py` file to your desired directory.

### Step 3: Configure with Smithery

Add the server to your Smithery configuration file (`mcp.json`):

```json
{
  "mcpServers": {
    "stepstone-job-search": {
      "command": "python",
      "args": ["/path/to/stepstone_server.py"],
      "description": "Search for job listings on Stepstone.de"
    }
  }
}
```

### Step 4: Configure with Claude Desktop

If using Claude Desktop, add to your configuration file:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "stepstone-job-search": {
      "command": "python",
      "args": ["/path/to/stepstone_server.py"]
    }
  }
}
```

## Usage

### Available Tools

#### `search_jobs`

Search for job listings using multiple search terms.

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

#### Fraud/Compliance Specialist Search
```json
{
  "tool": "search_jobs",
  "parameters": {
    "search_terms": ["fraud", "betrug", "compliance", "risk management"],
    "zip_code": "40210",
    "radius": 25
  }
}
```

### Sample Output

```
Job Search Summary:
Search Terms: fraud, betrug
Location: 40210 (±5km)
Total Jobs Found: 15

--- Results for 'fraud' ---

1. Senior Fraud Analyst
   Company: Deutsche Bank AG
   Location: Düsseldorf
   Link: https://www.stepstone.de/stellenangebote--Senior-Fraud-Analyst-Dusseldorf-Deutsche-Bank-AG--9234567

2. Fraud Prevention Specialist
   Company: PayPal Europe
   Location: Düsseldorf
   Link: https://www.stepstone.de/stellenangebote--Fraud-Prevention-Specialist-Dusseldorf-PayPal-Europe--9234568

--- Results for 'betrug' ---

3. Betrugsermittler (m/w/d)
   Company: Allianz Versicherung
   Location: Düsseldorf
   Link: https://www.stepstone.de/stellenangebote--Betrugsermittler-Dusseldorf-Allianz--9234569
```

## Available Resources

The server provides built-in documentation accessible through the resource system:

- `stepstone://search-help`: Complete usage guide and examples

## German Postal Code Examples

| City | Postal Code | Area |
|------|-------------|------|
| Berlin | 10115 | Berlin Mitte |
| Munich | 80331 | Munich Center |
| Hamburg | 20095 | Hamburg Center |
| Cologne | 50667 | Cologne Center |
| Frankfurt | 60329 | Frankfurt Center |
| Düsseldorf | 40210 | Düsseldorf Center |
| Stuttgart | 70173 | Stuttgart Center |

## Troubleshooting

### Common Issues

#### Server Not Starting
- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Check Python version: `python --version` (requires 3.8+)
- Verify file path in configuration is correct

#### No Jobs Found
- Check if the postal code is valid (5-digit German postal code)
- Try broader search terms or increase radius
- Verify internet connection
- Check Stepstone.de website is accessible

#### Import Errors
```bash
# Install missing dependencies
pip install requests beautifulsoup4 mcp lxml
```

#### Permission Errors
```bash
# On Unix systems, make the script executable
chmod +x stepstone_server.py
```

### Logging

The server includes comprehensive logging. To see debug information:

1. Set logging level in the script:
```python
logging.basicConfig(level=logging.DEBUG)
```

2. Or run with verbose output:
```bash
python stepstone_server.py --verbose
```

## Rate Limiting and Ethics

This server includes built-in rate limiting and respectful scraping practices:

- Uses appropriate User-Agent headers
- Implements request timeouts
- Handles errors gracefully
- Respects website structure

**Please use responsibly** and in accordance with Stepstone.de's terms of service.

## Development

### Project Structure
```
stepstone-mcp-server/

├── stepstone_server.py    # Main MCP server


├── requirements.txt       # Python dependencies



├── mcp.json              # Smithery configuration



├── README.md             # This file




└── examples/             # Usage examples




```

### Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

### Testing

To test the server locally:

```bash
# Test basic functionality
python stepstone_server.py





# Test with specific parameters
echo '{"search_terms": ["test"], "zip_code": "40210"}' | python stepstone_server.py




```

## License

MIT License - see LICENSE file for details.

## Support

For issues and questions:
- Check the troubleshooting section above
- Review the server logs for error messages
- Ensure your MCP client (Smithery/Claude Desktop) is properly configured

## Version History

- **v1.0.0**: Initial release with basic job search functionality
- Support for multiple search terms
- Location-based search with postal codes
- Configurable search radius
- Comprehensive error handling

## Related Projects

- [Model Context Protocol](https://github.com/modelcontextprotocol/specification)
- [Smithery](https://smithery.ai/) - MCP client for AI assistants



- [Claude Desktop](https://claude.ai/desktop) - Desktop client with MCP support







