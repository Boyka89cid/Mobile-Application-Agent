# from mcp.server.fastmcp import FastMCP

# def resources(mcp: FastMCP):
#     @mcp.resource("ui://charts/app", mime_type="text/html;profile=mcp-app")
#     async def charts_app() -> str:
#         return """<!doctype html>
# <html>
# <head>
#   <meta charset="utf-8" />
#   <meta name="viewport" content="width=device-width, initial-scale=1" />
#   <style>
#     body { margin:0; padding:16px; font-family:system-ui; }
#     img { width:100%; height:auto; border-radius:12px; border:1px solid rgba(0,0,0,.12); }
#   </style>
# </head>
# <body>
#   <h3 id="title">Chart</h3>
#   <img id="img" />
#   <div id="status" style="opacity:.7;font-size:12px;margin-top:8px;">Waiting for data…</div>

#   <script>
#     // mcp-ui hosts send initial render data via postMessage
#     window.addEventListener("message", (event) => {
#       const msg = event?.data;
#       if (msg?.type === "mcp-ui-initial-render-data") {
#         const payload = msg.payload || {};
#         document.getElementById("title").textContent = payload.title || "Chart";
#         if (payload.pngBase64) {
#           document.getElementById("img").src = "data:image/png;base64," + payload.pngBase64;
#           document.getElementById("status").textContent = "✅ loaded";
#         } else {
#           document.getElementById("status").textContent = "❌ missing pngBase64";
#         }
#       }
#     });
#   </script>
# </body>
# </html>"""


# # from mcp.server.fastmcp import FastMCP
# # from tools.figureOchestrator.figOchestrationTools import CHART_IMAGE_BYTES

# # def resources(mcp: FastMCP):
# #     @mcp.resource("ui://charts/app", mime_type="text/html;profile=mcp-app")
# #     async def charts_app() -> str:
# #         return "<!doctype html><html><body><h3>Charts App OK</h3></body></html>"
# # def resources(mcp: FastMCP):
# #     @mcp.resource("ui://charts/app", mime_type="text/html;profile=mcp-app")
# #     async def charts_app() -> str:
# #         return """<!doctype html>
# #     <html>
# #     <head>
# #     <meta charset="utf-8" />
# #     <meta name="viewport" content="width=device-width, initial-scale=1" />
# #     <style>
# #         body { margin: 0; padding: 16px; font-family: system-ui; }
# #         img { width: 100%; height: auto; border-radius: 12px; border: 1px solid rgba(0,0,0,.12); }
# #     </style>
# #     </head>
# #     <body>
# #     <h3>Bar Chart</h3>
# #  <img id="plot" />
# #  <img src="http://127.0.0.1:8001/bar_chart_1.png" />
# #  <img src="file:///Users/kushaldevgun/Downloads/bar_chart_1.png" />
# # <script>
# #   const img = document.getElementById("plot");
# #   img.src = "file:///Users/kushaldevgun/Downloads/bar_chart_1.png";

# #   img.onload = () => document.body.insertAdjacentHTML("beforeend", "<p>✅ loaded</p>");
# #   img.onerror = () => document.body.insertAdjacentHTML("beforeend", "<p>❌ blocked / not found</p>");
# # </script>


# #     </body>
# #     </html>"""



# #     @mcp.resource("ui://charts/app", mime_type="text/html;profile=mcp-app")
# #     async def charts_app() -> str:
# #         return """<!doctype html>
# #         <html>
# #         <head>
# #         <meta charset="utf-8" />
# #         <meta name="viewport" content="width=device-width, initial-scale=1" />
# #         <style>
# #             body { margin: 0; padding: 16px; font-family: system-ui; }
# #             img { width: 100%; height: auto; border-radius: 12px; border: 1px solid rgba(0,0,0,.12); }
# #             .muted { opacity: .7; font-size: 12px; margin-top: 8px; }
# #             code { background: rgba(0,0,0,.06); padding: 2px 6px; border-radius: 6px; }
# #         </style>
# #         </head>
# #         <body>
# #         <h3 id="title">Bar Chart</h3>
# #         <div class="muted" id="status">Waiting for sid man…</div>
# #         <img id="plot" />

# #         <script>
# #   const sid = new URLSearchParams(location.search).get("sid");

# #   if (sid) {
# #     document.getElementById("plot").src =
# #       `ui://charts/image/${sid}.png`;
# #   } else {
# #     document.body.insertAdjacentHTML(
# #       "beforeend",
# #       "<p>Missing sid</p>"
# #     );
# #   }
# # </script>
# #         </body>
# #         </html>"""

#     # @mcp.resource("ui://charts/image/{sid}.png", mime_type="image/png")
#     # async def chart_image(sid: str) -> bytes:
#     #     with open(f"/tmp/{sid}.png", "rb") as f:
#     #         return f.read()

# #     async def charts_app() -> str:
# #         return """<!doctype html>
# # <html>
# # <head>
# #   <meta charset="utf-8" />
# #   <meta name="viewport" content="width=device-width, initial-scale=1" />
# #   <style>
# #     body { margin: 0; padding: 16px; font-family: system-ui; }
# #     img { width: 100%; height: auto; border-radius: 12px; border: 1px solid rgba(0,0,0,.12); }
# #   </style>
# # </head>
# # <body>
# #   <h3>Bar Chart</h3>
# #   <img id="plot" />
# #   <script>
# #     const sid = new URLSearchParams(location.search).get("sid");
# #     if (sid) {
# #       document.getElementById("plot").src = `ui://charts/image/${sid}.png`;
# #     } else {
# #       document.body.insertAdjacentHTML("beforeend", "<p>Missing sid</p>");
# #     }
# #   </script>
# # </body>
# # </html>"""

#     # @mcp.resource("ui://charts/image/{sid}.png", mime_type="image/png")
#     # async def chart_image(sid: str) -> bytes:
#     #     png_bytes = CHART_IMAGE_BYTES.get(sid)
#     #     if not png_bytes:
#     #         raise ValueError(f"No chart found for sid={sid}")
#     #     return png_bytes



# # resources/chartsResources.py
# # from pathlib import Path
# # from mcp.server.fastmcp import FastMCP
# # from mcp.types import TextResourceContents

# # def resources(mcp: FastMCP):
# #     # Use @mcp.resource(...) so FastMCP creates a Resource WITH a read() method internally.
# #     @mcp.resource("ui://charts/app", mime_type="text/html;profile=mcp-app")
# #     def charts_ui() -> TextResourceContents:
# #         html_path = Path(__file__).parent / "charts_app.html"
# #         html = html_path.read_text(encoding="utf-8")

# #         return TextResourceContents(
# #             uri="ui://charts/app",
# #             mimeType="text/html;profile=mcp-app",
# #             text=html,
# #         )


# # from pathlib import Path
# # from mcp.server.fastmcp import FastMCP
# # from mcp.types import TextResourceContents

# # class ChartsResources:
# #     def __init__(self, mcp: FastMCP):
# #         self.mcp = mcp

# #     # def get_charts_ui(self) -> str:
# #     #     html_path = Path(__file__).parent / "charts_app.html"
# #     #     return html_path.read_text(encoding="utf-8")

# # def resources(mcp: FastMCP):
# #     # res = ChartsResources(mcp = mcp)

# #     # Use @mcp.resource(...) so FastMCP creates a Resource WITH a read() method internally.
# #     @mcp.resource("ui://charts/app", mime_type="text/html;profile=mcp-app")
# #     def charts_ui() -> TextResourceContents:
# #         html_path = Path(__file__).parent / "charts_app.html"
# #         html = html_path.read_text(encoding="utf-8")
# #         return html
# #         # return TextResourceContents(
# #         #     uri="ui://charts/app",
# #         #     mimeType="text/html;profile=mcp-app",
# #         #     text=html,
# #         # )