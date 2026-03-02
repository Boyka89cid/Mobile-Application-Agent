# from mcp_ui_server import create_ui_resource

# # Inline HTML
# html_resource = create_ui_resource({
#   "uri": "ui://greeting/1",
#   "content": { "type": "rawHtml", "htmlString": "<p>Hello, from Python!</p>" },
#   "encoding": "text",
# })

# import base64
# from mcp.types import EmbeddedResource
# from resources.chartsResources import create_ui_resource

# def create_png_html_app(uri: str, title: str, png_bytes: bytes) -> EmbeddedResource:
#     b64 = base64.b64encode(png_bytes).decode("ascii")

#     html = f"""<!doctype html>
# <html>
# <head>
# <meta charset="utf-8"/>
# <meta name="viewport" content="width=device-width, initial-scale=1"/>
# <style>
#   body {{ margin:0; padding:16px; font-family:system-ui; }}
#   img {{ width:100%; height:auto; border-radius:12px; border:1px solid rgba(0,0,0,.12); }}
# </style>
# </head>
# <body>
#   <h3>{title}</h3>
#   <img src="data:image/png;base64,{b64}" />
# </body>
# </html>"""

#     return create_ui_resource({
#         "uri": uri,
#         "content": {"type": "rawHtml", "htmlString": html},
#         "encoding": "text",
#     })
