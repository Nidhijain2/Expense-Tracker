from db import init_db
from tools import mcp

# Initialize DB

init_db()

# Start MCP server

if __name__ == "__main__":

    mcp.run(
        transport="streamable-http",
        host="0.0.0.0",
        port=8000
    )