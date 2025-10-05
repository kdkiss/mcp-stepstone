<h1 align="center">Stepstone MCP Server</h1>
<p align="center"><em>Fast, structured job search for MCP-native clients.</em></p>

<p align="center">
  <a href="https://www.python.org/"><img alt="Python" src="https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white"></a>
  <a href="https://github.com/modelcontextprotocol/"><img alt="MCP" src="https://img.shields.io/badge/Protocol-MCP-7B61FF"></a>
  <a href="LICENSE"><img alt="License" src="https://img.shields.io/badge/License-MIT-2C3E50"></a>
</p>

---

### Quick Start

```bash
pip install -r requirements.txt
python stepstone_server.py
```

### Example

```bash
# Search Stepstone for remote data roles around Berlin
tool_call("search_jobs", {
  "search_terms": ["data engineer", "analytics"],
  "location": {"postal_code": "10115", "radius_km": 25}
})
```

### Docs

Full guides and API notes live in the [docs/](docs/) directory.

### Contributing

Pull requests welcome—open an issue first for major ideas, then ship focused commits with tests.

### License

Released under the MIT License. See [LICENSE](LICENSE).
