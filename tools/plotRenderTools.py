# from __future__ import annotations
# import base64
# from typing import Any, Literal, Optional, Dict, Annotated
# from pydantic import BaseModel, AnyUrl, Field
# from mcp.types import EmbeddedResource, TextResourceContents, BlobResourceContents
# from mcp.server.fastmcp import FastMCP


# UI_METADATA_PREFIX = "ui:"  # you can pick your own, but keep consistent

# # ---- Pydantic option models (similar to the SDK) ----

# class RawHtmlPayload(BaseModel):
#     type: Literal["rawHtml"] = "rawHtml"
#     htmlString: str = Field(..., min_length=1)


# class ExternalUrlPayload(BaseModel):
#     type: Literal["externalUrl"] = "externalUrl"
#     iframeUrl: str = Field(..., min_length=1)


# class RemoteDomPayload(BaseModel):
#     type: Literal["remoteDom"] = "remoteDom"
#     framework: Literal["react", "webcomponents"]
#     script: str = Field(..., min_length=1)


# ContentPayload = Annotated[
#     RawHtmlPayload | ExternalUrlPayload | RemoteDomPayload,
#     Field(discriminator="type")
# ]


# class CreateUIResourceOptions(BaseModel):
#     uri: str
#     content: ContentPayload
#     encoding: Literal["text", "blob"] = "text"
#     uiMetadata: Optional[Dict[str, Any]] = None
#     metadata: Optional[Dict[str, Any]] = None


# # ---- Helper to prefix metadata like the SDK ----

# def _prefixed_meta(uiMetadata: Optional[dict], metadata: Optional[dict]) -> dict:
#     merged: dict[str, Any] = {}
#     if uiMetadata:
#         for k, v in uiMetadata.items():
#             merged[f"{UI_METADATA_PREFIX}{k}"] = v
#     if metadata:
#         merged.update(metadata)  # allow user metadata to override
#     return {"_meta": merged} if merged else {}


# # ---- This is your CreateUIResource-like function ----

# def create_ui_resource(options_dict: dict[str, Any]) -> EmbeddedResource:
#     opts = CreateUIResourceOptions.model_validate(options_dict)

#     if not opts.uri.startswith("ui://"):
#         raise ValueError(f"URI must start with ui://, got: {opts.uri}")

#     # Decide payload + mimetype based on content.type
#     c = opts.content
#     if c.type == "rawHtml":
#         actual = c.htmlString
#         mime = "text/html;profile=mcp-app"
#     elif c.type == "externalUrl":
#         actual = c.iframeUrl
#         mime = "text/uri-list"
#     elif c.type == "remoteDom":
#         actual = c.script
#         if c.framework == "react":
#             mime = "application/vnd.mcp-ui.remote-dom+javascript; framework=react"
#         else:
#             mime = "application/vnd.mcp-ui.remote-dom+javascript; framework=webcomponents"
#     else:
#         raise ValueError(f"Unsupported content type: {c.type}")

#     extra = _prefixed_meta(opts.uiMetadata, opts.metadata)

#     # Build the *resource contents* object
#     if opts.encoding == "text":
#         resource = TextResourceContents(
#             uri=AnyUrl(opts.uri),
#             mimeType=mime,
#             text=actual,
#             **extra,
#         )
#     else:
#         # blob encoding is base64 of utf-8 bytes
#         resource = BlobResourceContents(
#             uri=AnyUrl(opts.uri),
#             mimeType=mime,
#             blob=base64.b64encode(actual.encode("utf-8")).decode("ascii"),
#             **extra,
#         )

#     # Wrap as EmbeddedResource (MCP content item)
#     return EmbeddedResource(type="resource", resource=resource)

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
#     # def render_plot(self, image_path: str, title: str = "Plot") -> CallToolResult:
#     #     real_path = os.path.realpath(image_path)
#     #     if not os.path.isfile(real_path):
#     #         return CallToolResult(
#     #             content=[TextContent(type="text", text=f"File not found: {real_path}")],
#     #             isError=True,
#     #         )

#     #     mime, _ = mimetypes.guess_type(real_path)
#     #     if not mime:
#     #         mime = "image/png"

#     #     with open(real_path, "rb") as f:
#     #         b64 = base64.b64encode(f.read()).decode("utf-8")

#     #     return CallToolResult(
#     #         content=[TextContent(type="text", text="Rendered in panel.")],
#     #         structuredContent={
#     #             "kind": "plot",
#     #             "title": title,
#     #             "mimeType": mime,
#     #             "image_b64": b64,
#     #         },
#     #         isError=False,
#     #     )