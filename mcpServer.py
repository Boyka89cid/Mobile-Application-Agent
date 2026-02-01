from mcp.server.fastmcp import FastMCP
from tools import llmRouterTools, orchestrationTools, employeeTools
from resources import tablesResources

mcp = FastMCP(
    "HRAssistantServer",
    host="0.0.0.0",
    port=8000,
    json_response=True
    )

llmRouterTools.register_tools(mcp)
orchestrationTools.register_orchestration_tools(mcp)
employeeTools.register_employee_tools(mcp)
tablesResources.resources(mcp)

if __name__ == "__main__":
    mcp.run(transport='stdio')