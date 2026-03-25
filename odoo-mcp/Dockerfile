# Odoo MCP Server
# Model Context Protocol server for Odoo accounting integration

FROM python:3.12-slim

WORKDIR /app

# Install dependencies
RUN pip install jsonrpcclient requests flask

# Copy MCP server code
COPY odoo_mcp_server.py .
COPY requirements.txt .

RUN pip install -r requirements.txt

# Expose MCP port
EXPOSE 8809

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8809/health || exit 1

# Run server
CMD ["python", "odoo_mcp_server.py"]
