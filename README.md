# Mobile Application Agent (MCP Server)

A powerful MCP (Model Context Protocol) server designed to interface with PostgreSQL databases. This tool allows users to manage database schemas, visualize data, and perform human-in-the-loop operations via Claude Desktop.

---

## 🚀 Prerequisites

Before you begin, ensure you have the following installed:

* **[Claude Desktop](https://claude.ai/download)**
* **[PostgreSQL](https://www.postgresql.org/download/)** (Running and accessible)
* **[Conda](https://docs.conda.io/en/latest/miniconda.html)** (Miniconda recommended)
* **[DBeaver](https://dbeaver.io/)** (Recommended for visualizing your database)

---

## 🛠️ Installation

### Step 1: Clone or Download

Download the project files from this repository to your local machine and navigate into the project folder:

```bash
cd /path/to/Mobile-Application-Agent

```

### Step 2: Configure Database Credentials

Locate `utils/config.py`. Update the `DB_CONFIG` dictionary with your local PostgreSQL credentials.

> **⚠️ Security Warning:** Never commit your real database passwords to a public GitHub repository. Use environment variables if you plan to push your changes.

### Step 3: Setup Environment

Create and activate your Conda environment to ensure all dependencies are managed correctly:

```bash
# Create and activate
conda create -n agents python=3.12
conda activate agents

# Install requirements
pip install --upgrade pip
pip install -r requirements.txt

```

---

## ⚙️ Configuration (Claude Desktop)

To connect the server to Claude, you must update the Claude Desktop configuration file.

1. **Locate the config file:**
* **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
* **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`


2. **Add/Update the configuration:**
*Replace `/YourUsername/` with your actual system username.*

#### Option A: Using `uv` (Recommended)

```json
{
  "mcpServers": {
    "HRAssistantServer": {
      "command": "/Users/YourUsername/miniconda3/envs/agents/bin/uv",
      "args": [
        "run", "--frozen", "--with", "mcp[cli]", "mcp", "run",
        "/Users/YourUsername/Desktop/Mobile-Application-Agent/mcpServer.py"
      ],
      "env": {
        "PATH": "/Users/YourUsername/miniconda3/envs/agents/bin",
        "PYTHONPATH": "/Users/YourUsername/Desktop/Mobile-Application-Agent"
      }
    }
  }
}

```

#### Option B: Using Standard Python

```json
{
  "mcpServers": {
    "HRAssistantServer": {
      "command": "/Users/YourUsername/miniconda3/envs/agents/bin/python",
      "args": [
        "/Users/YourUsername/Desktop/Mobile-Application-Agent/mcpServer.py"
      ]
    }
  }
}

```

---

## 🚀 Running the Project

1. **Completely quit** Claude Desktop (Cmd+Q / Alt+F4).
2. **Restart** Claude Desktop.
3. Look for the "HRAssistantServer" icon or status in your MCP settings inside Claude.

### 🔍 Troubleshooting

* **Logs:** If the server fails to connect, open Claude Desktop and view logs (usually located in `~/Library/Logs/Claude/mcp-server-HRAssistantServer.log`).
* **Paths:** Ensure every path in your JSON config is an absolute path (starting from `/Users/...`).
* **Conda:** Ensure you activated the `agents` environment before starting any processes. If the paths are incorrect, Claude cannot find the Python interpreter.
* **Database:** Use **DBeaver** to verify your PostgreSQL instance is running and your credentials are correct.

---

### Additional Tips

* **Visualizing Data:** We recommend using DBeaver to inspect changes made to your database by the tools.
* **Human-in-the-Loop:** Many of our tools require explicit confirmation (e.g., typing 'YES') to perform destructive actions like `DROP TABLE`.


