from mcp.server.fastmcp import FastMCP
from tools.queryOrchestrator import orchestrationTools
from tools.figureOchestrator import figOchestrationTools

from resources import tablesResources
from tools import llmRouterTools

mcp = FastMCP(
    "HRAssistantServer",
    host="0.0.0.0",
    port=7677,
    json_response=True
    )

llmRouterTools.register_tools(mcp)
orchestrationTools.register_orchestration_tools(mcp)
figOchestrationTools.register_fig_orchestration_tools(mcp)
tablesResources.resources(mcp)

# @mcp.tool(description= "Image path should be relative to /Users/kushaldevgun/Downloads")
# def show_image(image_path: str, ctx: Context) -> ImageContent:
#     """Display a local image. Only the image."""

#     real_path = os.path.realpath(image_path)

#     # Restrict directory access
#     if not real_path.startswith(os.path.realpath(ALLOWED_DIR) + os.sep):
#         raise ValueError("Access denied: path not allowed")

#     if not os.path.isfile(real_path):
#         raise ValueError("File not found")

#     mime, _ = mimetypes.guess_type(real_path)
#     if not mime or not mime.startswith("image/"):
#         raise ValueError("Not a valid image")

#     with open(real_path, "rb") as f:
#         blob = f.read()

#     if len(blob) > 1_000_000:
#         raise ValueError("Image too large (>1MB)")

#     b64 = base64.b64encode(blob).decode("utf-8")

#     return ImageContent(
#         type="image",
#         data=b64,
#         mimeType=mime
#     )

if __name__ == "__main__":
    mcp.run(transport='stdio')