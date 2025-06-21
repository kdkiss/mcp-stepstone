## 📄 `README.md` — *mcp-stepstone*

# 🧠 mcp-stepstone

[![smithery badge](https://smithery.ai/badge/@kdkiss/mcp-stepstone)](https://smithery.ai/server/@kdkiss/mcp-stepstone)
**`mcp-stepstone`** is an MCP-compatible CLI module that fetches job listings from [Stepstone.de](https://www.stepstone.de) based on dynamic keywords and location parameters.

Designed to integrate seamlessly into autonomous agents or automation workflows using `stdin/stdout` for communication.


## 🚀 Features

- ✅ Fetches job listings dynamically from Stepstone.de
- ✅ Accepts input via stdin (JSON)
- ✅ Returns structured job results via stdout (JSON)
- ✅ Default fallbacks when no input is provided
- ✅ Works great with `npx`, `npm`, and `mcpServers` agent systems


## 📦 Installation & Usage

### Installing via Smithery

To install Stepstone Job Listings Fetcher for Claude Desktop automatically via [Smithery](https://smithery.ai/server/@kdkiss/mcp-stepstone):

```bash
npx -y @smithery/cli install @kdkiss/mcp-stepstone --client claude
```

### Installing manually
You can use it directly with `npx`:

```bash
npx mcp-stepstone
````

Or, install it globally:

```bash
npm install -g mcp-stepstone
```

Then call it:

```bash
echo '{}' | mcp-stepstone
```

---

## 🧾 Input Format (stdin)

Pass input as JSON via `stdin`:

```json
{
  "search_terms": ["fraud", "crime"],
  "zip_code": "40210",
  "radius": 5
}
```

### All fields are optional:

| Field          | Type       | Default                                            |
| -------------- | ---------- | -------------------------------------------------- |
| `search_terms` | `string[]` | `["fraud", "crime", "betrug", "fraud_specialist"]` |
| `zip_code`     | `string`   | `"40210"`                                          |
| `radius`       | `number`   | `5`                                                |

---

## 📤 Output Format (stdout)

Returns JSON of this shape:

```json
{
  "results": {
    "fraud": [
      {
        "title": "Senior Fraud Analyst",
        "company": "ABC GmbH",
        "location": "Düsseldorf",
        "link": "https://www.stepstone.de/job-id-xyz"
      },
      ...
    ],
    "crime": [
      ...
    ]
  }
}
```


## 🔌 Integration Example: `mcpServers` Config

```json
{
  "mcpServers": {
    "mcp-stepstone": {
      "command": "npx",
      "args": [
        "-y",
        "mcp-stepstone"
      ]
    }
  }
}
```


## 🛠 Development

To run locally:

```bash
npm install
echo '{}' | node index.js
```

Make sure you have Python 3 installed, as the core scraper is Python-based.


## 🧪 Roadmap Ideas

* [ ] Add output filtering (e.g. `--max=10`)
* [ ] Add file export support (`--output jobs.json`)
* [ ] Support non-German zip/postal codes
* [ ] Date-based filtering (if supported)







