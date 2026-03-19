from mcp.server.fastmcp import FastMCP
from tools.queryOrchestrator import orchestrationTools
from tools.figureOchestrator import figOchestrationTools
from resources import tablesResources
from tools import llmRouterTools

instructions = '''
    You are a helpful assistant for managing and querying databases. You have access to a set of tools that allow you to perform various operations on the PostgreSQL database.
    When a user asks you to perform an operation, you should determine which tool is appropriate for the task and use it to execute the operation. For more complex tasks, you may need to orchestrate multiple steps and tools to achieve the desired outcome.
    If user switches between different tools while the tool is running, you should be able to manage multiple sessions by resetting the state of the previous session and starting a new session for the new operation.
    '''

mcp = FastMCP(
    "HRAssistantServer",
    host="0.0.0.0",
    port=7677,
    json_response=True,
    instructions=instructions
    )


APP_URI = "ui://mcp-app-demo/main"
APP_HTML = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>MCP App Demo</title>
</head>
<body>
    <h1>Welcome to the MCP App Demo</h1>
    <p>This is a simple HTML app served by the MCP server.</p>
</body>
</html>"""

llmRouterTools.register_tools(mcp)
orchestrationTools.register_orchestration_tools(mcp)
figOchestrationTools.register_fig_orchestration_tools(mcp)
tablesResources.resources(mcp)

@mcp.resource("roots://list")
def list_roots():
    return {
        "roots": [
            {
                "uri": "file:///Users/kushaldevgun/Downloads/images/",
                "name": "Image Directory" 
            },
            ]
    }

if __name__ == "__main__":
    mcp.run()
    #asyncio.run(main())
    
# @mcp.tool("get_roots")
# def get_mcp_roots():
#     context = mcp.get_context()
#     session = context.session
    
#     roots = getattr(context, "roots", None) or getattr(context, "root_uris", None)
#     if not roots:
#         raise ValueError("No roots provided by client")

# @mcp.tool()
# def process_file(filename: str) -> str:
#     return f"Processing file: {filename}"

# @mcp.sse_app(APP_URI, mime_type="text/html;profile=mcp-app")
# async def demo_app():
#     return {
#         "contents": [{
#             "uri": APP_URI,
#             "mimeType": "text/html;profile=mcp-app",
#             "text": APP_HTML,
#             "_meta": {
#                 "ui": {
#                     "prefersBorder": True,
#                     "csp": {
#                         "connectDomains": [],
#                         "resourceDomains": [],
#                         "frameDomains": [],
#                         "baseUriDomains": [],
#                     }
#                 }
#             }
#         }]
#     }

# @mcp.resource("ui://dashboard/main/{x}", mime_type="text/html;profile=mcp-app")
# async def dashboard_main(x: int) -> str:
#     if x < 0:
#         raise ValueError("Input must be non-negative")
    
#     img_path = f"/Users/kushaldevgun/Downloads/images/bar_chart_1.png"
#     #plt.savefig(img_path, format="png")
#     with open(img_path, "rb") as f:
#         png_bytes = f.read()
#     b64 = base64.b64encode(png_bytes).decode("utf-8")
#     mime, _ = mimetypes.guess_type(img_path)
#     return f"""<html><body><h1>Dashboard</h1><img src="data:image/png;base64,{b64}" /></body></html>"""



# @mcp.tool("create_file")
# async def create_file(path: str, content: str):
#     # Convert to absolute path
#     abs_path = os.path.abspath(path)
    
#     with open(abs_path, 'w') as f:
#         f.write(content)
#     await mcp.get_context().session.send_log_message("info", f"File created at {abs_path}")
#     return {"success": True, "path": abs_path}

    # Check against allowed file system roots
    # for root in mcp.current_roots:
    #     if root.uri.startswith("file://"):
    #         root_path = root.uri.replace("file://", "")
    #         if abs_path.startswith(root_path):
    #             # Write the file
    #             with open(abs_path, 'w') as f:
    #                 f.write(content)
    #             return {"success": True, "path": abs_path}
 
    # return {
    #     "success": False,
    #     "error": "Permission denied: path is outside allowed roots"
    # }

# async def main():
#     async with stdio_server() as (read_stream, write_stream):
#         await mcp.run(
#             read_stream=read_stream,
#             write_stream=write_stream,
#             initialization_options=InitializationOptions(
#                 server_name="HRAssistantServer",
#                 server_version="1.0.0",
#                 description="MCP server for HR Assistant Agent",
#                 capabilities=["tool_execution", "structured_output"]
#             ),
#             # notification_options=NotificationOptions(
#             #     log_level="info",
#             #     log_to_console=True
#             # ),
#             # experimental_capabilities=["ui_rendering", "async_tools"]
#         )
