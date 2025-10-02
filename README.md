# Stepstone Job Search MCP Server

[![smithery badge](https://smithery.ai/badge/@kdkiss/mcp-stepstone)](https://smithery.ai/server/@kdkiss/mcp-stepstone)

An [Model Context Protocol (MCP)](https://github.com/modelcontextprotocol/specification) server that lets MCP-compatible clients search the German job portal [Stepstone.de](https://www.stepstone.de). The service exposes a pair of tools for running multi-term job searches and fetching rich job details so assistants such as Claude Desktop or Smithery can surface up-to-date vacancies.

---

## Table of Contents

1. [Key Features](#key-features)
2. [Quick Start](#quick-start)
3. [Configuration](#configuration)
4. [Usage](#usage)
5. [Architecture Overview](#architecture-overview)
6. [Local Development](#local-development)
7. [Testing](#testing)
8. [Troubleshooting](#troubleshooting)
9. [Contributing](#contributing)
10. [Support](#support)
11. [Version History](#version-history)
12. [License](#license)

---

## Key Features

- 🔍 **Multi-term Search** – Concurrently queries Stepstone for every search phrase you supply and deduplicates duplicate postings.
- 📍 **Location Targeting** – Supports German postal codes with a configurable radius (1–100 km) for regional searches.
- 🧠 **Session-aware Follow-ups** – Saves results for one hour so you can request full job details later via `get_job_details`.
- 🛡️ **Robust Validation** – Defensive parameter validation, logging, and graceful error messages for malformed requests.
- 🐳 **Container & CLI Friendly** – Works as a plain Python process or inside Docker; integrates cleanly with Smithery and Claude Desktop.

> ℹ️ **Note:** A Redis cache and other scaling features are mentioned as future enhancements. They are not enabled in the current release.

---

## Quick Start

### Prerequisites

- Python 3.8+
- `pip`
- Internet access to reach Stepstone.de when running real searches

### Installation Options

<details>
<summary><strong>Option 1 · Install with Smithery (Recommended)</strong></summary>

```bash
npx -y @smithery/cli install @kdkiss/mcp-stepstone --client claude
```

</details>

<details>
<summary><strong>Option 2 · Manual Setup</strong></summary>

```bash
# Clone the repository
git clone https://github.com/kdkiss/mcp-stepstone.git
cd mcp-stepstone

# Install runtime dependencies
pip install -r requirements.txt

# (Optional) make the server script executable on Unix-like systems
chmod +x stepstone_server.py
```

</details>

<details>
<summary><strong>Option 3 · Docker</strong></summary>

```bash
# Build the image
docker build -t mcp-stepstone .

# Run the container
docker run -it --rm mcp-stepstone
```

</details>

---

## Configuration

### MCP Client Configuration

#### Smithery `mcp.json`

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

#### Claude Desktop

- **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows:** `%APPDATA%/Claude/claude_desktop_config.json`

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
| --- | --- | --- |
| `LOG_LEVEL` | `INFO` | Logging verbosity (`DEBUG`, `INFO`, `WARNING`, `ERROR`). |
| `REQUEST_TIMEOUT` | `10` | Timeout (seconds) for outbound HTTP requests. |
| `USER_AGENT` | Browser-like UA string | Custom User-Agent presented to Stepstone.de. |
| `MAX_RETRIES` | `3` | Retry attempts for failed HTTP calls. |
| `CACHE_TTL` | `300` | Placeholder for future in-memory caching feature. |

---

## Usage

### Available Tools

#### `search_jobs`
Runs one or more keyword searches against Stepstone.

**Parameters**
- `search_terms` *(array of strings, optional)* – Search phrases to query. Defaults to `["fraud", "betrug", "compliance"]`.
- `zip_code` *(string, optional)* – German 5-digit postal code. Defaults to `"40210"` (Düsseldorf).
- `radius` *(integer, optional)* – Radius in kilometres around the postal code. Defaults to `5`; must be between 1 and 100.

#### `get_job_details`
Fetches one stored job and enriches it with full description and metadata.

**Parameters**
- `job_index` *(integer, optional)* – 1-based index into the most recent session’s results.
- `job_query` *(string, optional)* – Fuzzy match against stored jobs. Alias `query` is also accepted.
- `session_id` *(string, optional)* – Explicit session identifier (auto-selects the most recent active session when omitted).

> ⚠️ Provide either `job_index` or `job_query`. Supplying both prioritises `job_index`.

### Example Invocations

```jsonc
// Basic search
{
  "tool": "search_jobs",
  "parameters": {
    "search_terms": ["software engineer", "developer"]
  }
}

// Location constrained search
{
  "tool": "search_jobs",
  "parameters": {
    "search_terms": ["marketing manager", "digital marketing"],
    "zip_code": "10115",
    "radius": 15
  }
}

// Fetch job details by index
{
  "tool": "get_job_details",
  "parameters": {
    "job_index": 1
  }
}

// Fetch job details by query string
{
  "tool": "get_job_details",
  "parameters": {
    "job_query": "AML Specialist",
    "session_id": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

### Sample Output

```
Job Search Summary:
Search Terms: fraud analyst, compliance officer
Location: 60329 (±25km)
Total Jobs Found: 23
Session ID: 550e8400-e29b-41d4-a716-446655440000

--- Results for 'fraud analyst' ---

1. Senior Fraud Analyst - Digital Banking
   Company: Deutsche Bank AG
   Description: Join our fraud prevention team to analyze transaction patterns...
   Link: https://www.stepstone.de/stellenangebote--Senior-Fraud-Analyst-Frankfurt-Deutsche-Bank-AG--1234567
```

```
📋 Job Details: Senior Fraud Analyst - Digital Banking
🏢 Company: Deutsche Bank AG
📍 Location: Frankfurt am Main
💰 Salary: €65,000 - €85,000 per year
⏰ Employment Type: Full-time, Permanent

📝 Description:
Join our fraud prevention team to analyze transaction patterns and develop detection algorithms...

✅ Requirements:
  • Bachelor's degree in Computer Science, Finance, or related field
  • 3+ years experience in fraud detection or financial crime prevention
  • Strong analytical skills with SQL, Python, or R
  • Knowledge of AML regulations and compliance frameworks
```

---

## Architecture Overview

```
┌────────────────────┐    ┌─────────────────────┐    ┌───────────────────┐
│    MCP Client      │ ──▶ │  MCP Stepstone      │ ──▶ │   Stepstone.de     │
│ (Claude/Smithery)  │    │      Server          │    │    Job Portal      │
└────────────────────┘    └─────────────────────┘    └───────────────────┘
                                │
                        ┌─────────────────────┐
                        │   Job Scraper       │
                        │ - URL Builder       │
                        │ - HTML Parser       │
                        │ - Data Cleaner      │
                        └─────────────────────┘
```

1. **Request** – MCP client sends tool invocation.
2. **Validation** – Inputs validated (terms, postal code, radius).
3. **Search** – URLs constructed and fetched concurrently.
4. **Processing** – HTML parsed and normalised job entries produced.
5. **Sessioning** – Results stored in memory for one hour for follow-up queries.
6. **Response** – Textual summary returned to the MCP client.
7. **Details** – `get_job_details` fetches the original job page and extracts specifics.

Key modules:
- `StepstoneJobScraper` – Builds search URLs, fetches and parses job listings.
- `JobDetailParser` – Scrapes detailed job pages for salary, requirements, etc.
- `SessionManager` – Stores search sessions, supports lookup by index or fuzzy match.
- `stepstone_server.py` – Registers MCP tools/resources and handles tool invocations.

---

## Local Development

```bash
# Clone repository
git clone https://github.com/kdkiss/mcp-stepstone.git
cd mcp-stepstone

# Create & activate a virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install dev tooling
pip install pytest pytest-asyncio black flake8

# Run formatter and linter
black stepstone_server.py
flake8 stepstone_server.py
```

### Debug Fixtures

A lightweight HTTP server is included to serve bundled HTML fixtures. Start it when adjusting selectors or parsers:

```bash
python debug_server.py
```

Visit `http://127.0.0.1:5000` to inspect the mocked Stepstone pages used in tests.

---

## Testing

The test suite uses mocked network responses to avoid contacting Stepstone.de.

```bash
pip install -r requirements.txt pytest
pytest
```

To validate specific tool flows interactively, you can run `stepstone_server.py` directly or call `handle_call_tool` from a Python shell.

---

## Troubleshooting

### Server Won’t Start

```bash
python --version            # Expect 3.8+
pip list | grep -E "(requests|beautifulsoup4|mcp)"
ls -la stepstone_server.py   # Confirm execute permissions when running directly
```

### No Jobs Returned

- Verify the postal code is a valid five-digit German PLZ.
- Increase `radius` or broaden `search_terms`.
- Confirm internet connectivity.
- Stepstone layout changes may require updating selectors—use the debug server to compare fixtures.

### Import Errors

```bash
pip install -r requirements.txt
pip install --upgrade pip
```

### Enable Verbose Logging

```bash
export LOG_LEVEL=DEBUG
python stepstone_server.py
```

Logs are emitted to stdout; integrate with your own logging infrastructure if desired.

---

## Contributing

1. Fork the repository and create a feature branch: `git checkout -b feature/my-change`.
2. Implement your changes and add tests.
3. Run `pytest` and lint/format the code (`black`, `flake8`).
4. Open a pull request describing the change.

Coding guidelines:
- Follow PEP 8 and include type hints where practical.
- Document public functions with docstrings.
- Handle network and parsing errors defensively.

---

## Support

- 📖 Consult this README for configuration and usage tips.
- 🧪 Use the debug server to inspect fixture HTML when selectors break.
- 🐛 File bugs or feature requests via GitHub Issues.
- 💬 Join the project’s Discord community (link forthcoming).

---

## Version History

### v1.2.0 (Current)
- Added `get_job_details` tool for follow-up queries.
- Introduced session management with one-hour TTL.
- Enhanced detail parsing for salary, requirements, and benefits.
- Summaries now include session IDs for easy follow-up.

### v1.1.0
- Expanded documentation and usage examples.
- Added Docker support and environment variable configuration.
- Improved error handling and validation.

### v1.0.0
- Initial release with multi-term job search and MCP compliance.

---

## License

Distributed under the [MIT License](LICENSE).

---

**Made with ❤️ for the German job market.**
