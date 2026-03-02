
from mcp.server.fastmcp import FastMCP
import matplotlib.pyplot as plt, io, base64, mimetypes
from mcp.types import ImageContent
class FigureHelperFxns:
    """
    This class contains helper functions for the figure orchestration process, such as generating histograms and displaying dashboards.
    """

    def draw_bar_plot(self, table_name: str, column_name: str, unique_values: list, counts: list):
        plt.rcParams['svg.fonttype'] = 'none'
        plt.figure(figsize=(10, 6))
        plt.bar(unique_values, counts)
        plt.xlabel(column_name, fontsize=12)
        plt.ylabel("Values", fontsize=12)
        plt.title(f'Bar Chart of {column_name} in {table_name}', fontsize=14)

        #plt.tight_layout()
        #sid = sessions.session_id
        #buf = io.BytesIO()

        png_img_path = f"/Users/kushaldevgun/Downloads/images/bar_chart.png"
        svg_img_path = f"/Users/kushaldevgun/Downloads/images/bar_chart.svg" # Used for Dashboard rendering, but not returned to user directly since some clients may not support SVG rendering
        plt.savefig(png_img_path, format = 'png')
        plt.savefig(svg_img_path, format="svg", bbox_inches='tight')
        plt.close()
        with open(png_img_path, "rb") as f:
            png_bytes = f.read()
        b64 = base64.b64encode(png_bytes).decode("utf-8")
        mime, _ = mimetypes.guess_type(png_img_path)
        return ImageContent(
            type="image",
            mimeType=mime,
            data=b64,
        )
    
    def plot_pie_chart(self, table_name: str, category_column: str, unique_values: list, counts: list, session_id: str):
        plt.figure(figsize=(10, 6))
        plt.pie(counts, labels=unique_values, autopct='%1.1f%%', startangle=140)
        plt.title(f'Distribution of {category_column} in {table_name}')
        
        png_img_path = f'/Users/kushaldevgun/Downloads/pie_chart.png'
        svg_img_path = f'/Users/kushaldevgun/Downloads/pie_chart.svg'
        plt.savefig(png_img_path, format='png')
        plt.savefig(svg_img_path, format="svg", bbox_inches='tight')
        plt.close()

        # Reuse your existing base64 encoding logic
        with open(png_img_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("utf-8")
        
        return ImageContent(type="image", data=b64, mimeType="image/png")

    def plot_histogram(self, table_name: str, numeric_column: str, bins: int, session_id: str, data: list[float]):
        plt.figure(figsize=(10, 6))
        plt.hist(data, bins=bins, color='skyblue', edgecolor='black')
        plt.title(f'Frequency Distribution of {numeric_column} in {table_name}')
        plt.xlabel(numeric_column)
        plt.ylabel('Frequency')
        
        png_img_path = f'/Users/kushaldevgun/Downloads/histogram.png'
        svg_img_path = f'/Users/kushaldevgun/Downloads/histogram.svg'
        plt.savefig(png_img_path, format='png')
        plt.savefig(svg_img_path, format="svg", bbox_inches='tight')
        plt.close()

        # Encode to base64 using established project patterns
        with open(png_img_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("utf-8")
    
        return ImageContent(type="image", data=b64, mimeType="image/png")

# try:
#     sse_url ="http://127.0.0.1:6274/sse"
#     async with sse_client(sse_url) as streams:
#         print("SSE connection established.")
#         read_stream, write_stream = streams
#         async with ClientSession(read_stream, write_stream) as session:
#             print("ClientSession created.")
#             try:
#                 print("--> Calling session.initialize()...")
#                 await session.initialize() # <----- Explicit call added here!!!
#                 await self.mcp.get_context().session.send_log_message("critical", "Session initialized successfully.")
#                 print("<-- session.initialize() completed.")

#                 # Now safe to proceed with tool calls
#                 print("Session initialized, safe to call tools.")
#                 try:
#                     async with Client("http://127.0.0.1:6274", roots=["file:///Users/kushaldevgun/Downloads/images"]) as client:
#                         # Call a tool on the server
#                         result = await client.call_tool("create_file", {"path": img_path, "content": b64})
#                         await self.mcp.get_context().session.send_log_message("critical", f"Tool call result: {result}")
#                 except Exception as e:
#                     logging.error(f"Error calling create_file tool: {e}")
#                     await self.mcp.get_context().session.send_log_message("critical", f"Error calling create_file tool: {e}")
#                     return text("Failed to save the generated chart image.", is_error=True)
#                 # Example tool call:
#                 # response = await session.call_tool("some_tool", {"arg": "value"})
#                 # print(f"Tool response: {response}")

#             except Exception as init_error:
#                 print(f"Error during session.initialize(): {init_error}")
# except Exception as conn_error:
#     print(f"Connection error: {conn_error}")