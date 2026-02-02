import logging, sys
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)],
    force=True,
)

logger = logging.getLogger("HRAssistantServer")
logger.info("Server starting...")

from mcp.server.fastmcp import FastMCP
from tools import llmRouterTools, orchestrationTools
from resources import tablesResources

mcp = FastMCP(
    "HRAssistantServer",
    host="0.0.0.0",
    port=8000,
    json_response=True
    )

llmRouterTools.register_tools(mcp)
orchestrationTools.register_orchestration_tools(mcp)
tablesResources.resources(mcp)

if __name__ == "__main__":
    mcp.run(transport='stdio')