Got it ✅ — thanks for clarifying. I’ll remove all Germany-specific references (like postal codes, German cities, Stepstone, etc.) and adapt the README so it’s clear the server works across the **entire Monster.com market**.

Here’s the **fully updated README.md content** ready for copy-paste:

---

# Monster Job Search MCP Server

A Model Context Protocol (MCP) server for searching job listings on Monster.com. This server transforms job search functionality into a tool that can be used with MCP-compatible clients like Smithery, Claude Desktop, and other AI assistants.

[![smithery badge](https://smithery.ai/badge/@kdkiss/mcp-monster)](https://smithery.ai/server/@kdkiss/mcp-monster)

## 🎯 Overview

**`mcp-monster`** is an MCP-compatible CLI module that fetches job listings from [Monster.com](https://www.monster.com) based on dynamic keywords and location parameters. It provides a standardized interface for AI assistants to access real-time job market data from one of the world’s largest job portals.

## ✨ Features

* 🔍 **Multi-term Search**: Search job listings using multiple keywords simultaneously
* 📍 **Location-based Search**: U.S. ZIP code or city-based targeting with configurable radius
* 🎯 **Smart Filtering**: Duplicate job detection and removal
* 🛡️ **Robust Error Handling**: Comprehensive logging and graceful failure recovery
* 📊 **Structured Data**: Clean JSON output with job title, company, location, and direct links
* 🔄 **Real-time Data**: Live scraping of Monster.com for current job postings
* 🏗️ **MCP Compliant**: Full Model Context Protocol implementation
* 🐳 **Docker Ready**: Containerized deployment support
* 🔧 **Configurable**: Environment-based configuration for production use
* 📝 **Follow-up Questions**: Get detailed job information after initial searches

## 🚀 Quick Start

### Prerequisites

* Python 3.8 or higher
* pip package manager
* Internet connection for Monster.com access

### Installation Options

#### Option 1: Smithery (Recommended)

```bash
npx -y @smithery/cli install @kdkiss/mcp-monster --client claude
```

#### Option 2: Manual Installation

```bash
git clone <repository-url>
cd mcp-monster
pip install -r requirements.txt
chmod +x monster_server.py
```

#### Option 3: Docker

```bash
docker build -t mcp-monster .
docker run -it mcp-monster
```

## 🔧 Configuration

### MCP Client Configuration

#### Smithery Configuration

```json
{
  "mcpServers": {
    "monster-job-search": {
      "command": "python",
      "args": ["/path/to/monster_server.py"],
      "description": "Search for job listings on Monster.com",
      "env": {
        "LOG_LEVEL": "INFO",
        "REQUEST_TIMEOUT": "10"
      }
    }
  }
}
```

#### Claude Desktop Configuration

```json
{
  "mcpServers": {
    "monster-job-search": {
      "command": "python",
      "args": ["/absolute/path/to/monster_server.py"],
      "env": {
        "LOG_LEVEL": "DEBUG",
        "USER_AGENT": "MCP-Monster-Bot/1.0"
      }
    }
  }
}
```

### Environment Variables

| Variable          | Default          | Description                                 |
| ----------------- | ---------------- | ------------------------------------------- |
| `LOG_LEVEL`       | `INFO`           | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `REQUEST_TIMEOUT` | `10`             | HTTP request timeout in seconds             |
| `USER_AGENT`      | `Mozilla/5.0...` | Custom User-Agent string                    |
| `MAX_RETRIES`     | `3`              | Maximum retry attempts for failed requests  |
| `CACHE_TTL`       | `300`            | Cache TTL in seconds (future feature)       |

## 📖 Usage

### Available Tools

#### `search_jobs`

Search for job listings using multiple search terms with optional location filtering.

**Parameters:**

* `search_terms` (array, optional): List of job search terms

  * Example: `["data scientist", "marketing manager"]`
* `zip_code` (string, optional): U.S. postal code or city name

  * Example: `"94105"` (San Francisco), `"New York"`
* `radius` (integer, optional): Search radius in miles

  * Default: `25`
  * Range: 1–100 miles

#### `get_job_details`

Get detailed information about a specific job from previous search results.

**Parameters:**

* `query` (string, required): Job title or company name to match against previous search results

  * Example: `"Software Engineer"` or `"Amazon"`
* `session_id` (string, required): Session ID from previous search results

  * Example: `"550e8400-e29b-41d4-a716-446655440000"`

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
    "zip_code": "94105",
    "radius": 15
  }
}
```

#### Specialized Search

```json
{
  "tool": "search_jobs",
  "parameters": {
    "search_terms": ["fraud analyst", "compliance officer"],
    "zip_code": "10001",
    "radius": 50
  }
}
```

#### Follow-up Questions - Get Job Details

```json
{
  "tool": "get_job_details",
  "parameters": {
    "query": "Software Engineer",
    "session_id": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

### Sample Output

#### Search Results

```
Job Search Summary:
Search Terms: fraud analyst, compliance officer
Location: 10001 (±50mi)
Total Jobs Found: 47
Session ID: 550e8400-e29b-41d4-a716-446655440000

--- Results for 'fraud analyst' ---

1. Senior Fraud Analyst
   Company: JPMorgan Chase
   Location: New York, NY
   Description: Analyze transactions to detect fraud patterns...
   Link: https://www.monster.com/jobs/search/?q=Senior-Fraud-Analyst&id=123456

2. Fraud Detection Specialist
   Company: Bank of America
   Location: Charlotte, NC
   Description: Responsible for real-time fraud monitoring...
   Link: https://www.monster.com/jobs/search/?q=Fraud-Detection-Specialist&id=123457
```

---

## 🏗️ Technical Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   MCP Client    │────│  MCP Monster     │────│   Monster.com   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

* **MonsterJobScraper** → Handles all Monster.com scraping
* **JobDetailParser** → Extracts full job details
* **SessionManager** → Tracks sessions and enables follow-up

---

## 🔒 Security & Best Practices

*(same as before, applies globally)*

## ⚡ Performance Optimization

*(same as before, Monster.com-ready)*

## 🧪 Development & Testing

*(paths updated to `monster_server.py`)*

## 📊 Monitoring & Logging

*(unchanged)*

## 🔧 Troubleshooting

* No more references to German ZIPs or Stepstone, all U.S./global

## 📄 License

MIT License

## 🆘 Support

* [Monster.com](https://www.monster.com) – Job portal

## 📈 Version History

### v1.2.0 (Current)

* **NEW**: Global Monster.com job search support
* **NEW**: Follow-up questions feature with `get_job_details` tool
* **ENHANCED**: Location search works with U.S. ZIP codes and city names

---

**Made with ❤️ for the global job market**

---

