from dataclasses import dataclass
from mcp.server.fastmcp import FastMCP
import inspect, logging
from typing import Dict, Any
from mcp.types import ImageContent
from mcp_ui_server import   UIResource
from tools.figureOchestrator.figToolDescriptions import FigToolPrompts
from adapters.postgresAdapter import PostgresAdapter
from tools.figureOchestrator.figureHelperFxns import FigureHelperFxns
from tools.queryOrchestrator.postgresHelperFxns import PostgresHelperFxns
from utils.config import Configuration
from resources.dashboardResources import DashboardHelper
from tools.figureOchestrator.figSessionDataClasses import (
    BarChartSessionState, 
    PieChartSessionState, 
    HistogramSessionState
)
from tools.figureOchestrator.figSessionSteps import (
    BarChartSteps, 
    PieChartSteps, 
    HistogramSteps
)
from mcp_ui_server import create_ui_resource

def register_fig_orchestration_tools(mcp: FastMCP):
    adapter = PostgresAdapter(config=Configuration.DB_CONFIG)
    figure_tools = FigOchestrationTools(mcp, adapter)
    available_tools = [name for name, func in inspect.getmembers(figure_tools, predicate=inspect.ismethod) if not name.startswith('_')]
    #logging.info(f"Available figure orchestration tools: {available_tools}")
    for tool_name in available_tools:
        logging.info(f"Registering figure orchestration tool: {tool_name}")
        mcp.add_tool(
                getattr(figure_tools, tool_name),
                name=tool_name,
                description=getattr(FigToolPrompts, tool_name, "No description available.")
        )

BARCHARTSESSION : Dict[str, BarChartSessionState] = {}
PIECHARTSESSION: Dict[str, PieChartSessionState] = {}
HISTOGRAMSESSION: Dict[str, HistogramSessionState] = {}

class FigOchestrationTools:

    def __init__(self, mcp: FastMCP, adapter: PostgresAdapter):
        self.mcp = mcp
        self.adapter = adapter

    async def show_dashboard(self) -> list[UIResource]:
        """Display a sample dashboard with metrics."""

        # TODO Need to set these path to an actual path for end user.
        svg_path = f"/Users/kushaldevgun/Downloads/images/bar_chart.svg"
        svg_code = None
        with open(svg_path, "rb") as f:
            svg_code = f.read()
        try:
            dashboard_html = DashboardHelper().generate_dashboard_html(svg_code)
            ui_resource = create_ui_resource({
                "uri": "ui://dashboard/main",
                "content": {
                    "type": "rawHtml",
                    "htmlString": dashboard_html
                },
                "encoding": "text",
            })
            return [ui_resource]
        except Exception as e:
            logging.error(f"Error processing image: {e}")
            await self.mcp.get_context().session.send_log_message("error", f"Error processing image: {e}")
            return [create_ui_resource({
                "uri": "ui://dashboard/error",
                "content": {
                    "type": "rawHtml",
                    "htmlString": f"<html><body><h1>Error loading dashboard</h1><p>{e}</p></body></html>"
                },
                "encoding": "text"
            })]
    
    async def plot_bar_chart(self, session_state: BarChartSessionState) ->  Dict[str, Any] | ImageContent:

        def decide_step(session_state: BarChartSessionState) -> str:
            has_table_name = bool(session_state.table_name)
            has_column_name = bool(session_state.column_name)
            if not has_table_name:
                return BarChartSteps.ASK_TABLE_NAME.value
            elif not has_column_name:
                return BarChartSteps.ASK_COLUMN.value
            else:
                return BarChartSteps.GENERATE_CHART.value

        sessions = BARCHARTSESSION.setdefault(session_state.session_id, session_state)
        if session_state.table_name is not None:
            sessions.table_name = session_state.table_name
        if session_state.column_name is not None:
            sessions.column_name = session_state.column_name

        sessions.step = decide_step(sessions)

        if sessions.step == BarChartSteps.ASK_TABLE_NAME.value:
            return {
                "status": "ask_table_name",
                "message": "Which table would you like to visualize with a bar chart?"
            }

        if sessions.step == BarChartSteps.ASK_COLUMN.value:
            ok = PostgresHelperFxns(adapter=self.adapter).check_table_exists(sessions.table_name)
            if not ok:
                BARCHARTSESSION.pop(sessions.session_id, None)
                return {"status": "error", "message": f'Table "{sessions.table_name}" does not exist. Please check the table name and try again.'}
            return {
                "status": "ask_column",
                "message": "Please provide the column for which you want to generate the bar chart."
                }

        if sessions.step == BarChartSteps.GENERATE_CHART.value:
            column_data = PostgresHelperFxns(adapter=self.adapter).fetch_column_data(sessions.table_name, sessions.column_name)
            if not column_data:
                return {
                    "status": "error",
                    "message": f'No data found for column "{sessions.column_name}" in table "{sessions.table_name}".'
                    }

            unique_values = [row[sessions.column_name] for row in column_data]
            counts = [row["count"] for row in column_data]
            
            try:
                img_content: ImageContent = FigureHelperFxns().draw_bar_plot(sessions.table_name, sessions.column_name, unique_values, counts)
                BARCHARTSESSION.pop(sessions.session_id, None)
                return img_content
            except Exception as e:
                logging.error(f"Error generating bar chart: {e}")
                await self.mcp.get_context().session.send_log_message("critical", f"Error generating bar chart: {e}")
                return {"status": "error", "message": "Failed to generate bar chart."}

    async def plot_pie_chart(self, session_state: PieChartSessionState) -> Dict[str, Any] | ImageContent:
        def decide_step(s: PieChartSessionState) -> str:
            if not s.table_name: return PieChartSteps.ASK_TABLE_NAME.value
            if not s.category_column: return PieChartSteps.ASK_CATEGORY_COLUMN.value
            return PieChartSteps.GENERATE_PIE_CHART.value

        session = PIECHARTSESSION.setdefault(session_state.session_id, session_state)
        if session_state.table_name: session.table_name = session_state.table_name
        if session_state.category_column: session.category_column = session_state.category_column
        
        session.step = decide_step(session)

        if session.step == PieChartSteps.ASK_TABLE_NAME.value:
            return {"status": "ask_table_name", "message": "Which table would you like to use for the pie chart?"}

        elif session.step == PieChartSteps.ASK_CATEGORY_COLUMN.value:
            if not PostgresHelperFxns(self.adapter).check_table_exists(session.table_name):
                PIECHARTSESSION.pop(session.session_id, None)
                return {"status": "error", "message": f"Table '{session.table_name}' does not exist."}
            return {"status": "ask_column", "message": "Which categorical column should define the pie slices?"}

        elif session.step == PieChartSteps.GENERATE_PIE_CHART.value:
            data = PostgresHelperFxns(self.adapter).fetch_column_data(session.table_name, session.category_column)
            if not data:
                return {"status": "error", "message": "No data found for visualization."}

            labels = [str(row[session.category_column]) for row in data]
            sizes = [row['count'] for row in data]

            try:
                img_content: ImageContent = FigureHelperFxns().plot_pie_chart(session.table_name, session.category_column, labels, sizes, session.session_id)
                PIECHARTSESSION.pop(session.session_id, None)
                return img_content
            except Exception as e:
                logging.error(f"Pie chart error: {e}")
                await self.mcp.get_context().session.send_log_message("critical", f"Error generating pie chart: {e}")
                return {"status": "error", "message": f"Failed to generate pie chart. error: {e}"}
    
    async def plot_histogram(self, session_state: HistogramSessionState) -> Dict[str, Any] | ImageContent:
        def decide_step(s: HistogramSessionState) -> str:
            if not s.table_name: return HistogramSteps.ASK_TABLE_NAME.value
            if not s.numeric_column: return HistogramSteps.ASK_NUMERIC_COLUMN.value
            return HistogramSteps.GENERATE_HISTOGRAM.value

        session = HISTOGRAMSESSION.setdefault(session_state.session_id, session_state)
        if session_state.table_name: session.table_name = session_state.table_name
        if session_state.numeric_column: session.numeric_column = session_state.numeric_column
        if session_state.bins: session.bins = session_state.bins
        
        session.step = decide_step(session)

        if session.step == HistogramSteps.ASK_TABLE_NAME.value:
            return {
                "status": "ask_table_name",
                "message": "Which table contains the numeric data for the histogram?"
                }

        elif session.step == HistogramSteps.ASK_NUMERIC_COLUMN.value:
            if not PostgresHelperFxns(self.adapter).check_table_exists(session.table_name):
                HISTOGRAMSESSION.pop(session.session_id, None)
                return {"status": "error", "message": f"Table '{session.table_name}' not found."}
            return {
                "status": "ask_column",
                "message": "Which numeric column would you like to analyze?"
                }

        elif session.step == HistogramSteps.GENERATE_HISTOGRAM.value:
            # Fetch raw data for the specific column
            query = f'SELECT "{session.numeric_column}" FROM "{session.table_name}" WHERE "{session.numeric_column}" IS NOT NULL;'
            results = self.adapter.execute_query(query)
            
            if not results:
                return {"status": "error", "message": "No numeric data found for this column."}

            data = [row[session.numeric_column] for row in results]

            try:
                img_content: ImageContent = FigureHelperFxns().plot_histogram(session.table_name, session.numeric_column, session.bins, session.session_id, data)
                HISTOGRAMSESSION.pop(session.session_id, None)
                return img_content
            except Exception as e:
                logging.error(f"Histogram error: {e}")
                await self.mcp.get_context().session.send_log_message("critical", f"Error generating histogram: {e}")
                return {"status": "error", "message": "Failed to generate histogram."}
            
        return {"status": "error", "message": "Invalid step in histogram generation process."}
        

    # async def show_new_dashboard(self):
    #     encoding = "text"
    #     mime_type = "text/html"

    #     html_document = """<!DOCTYPE html>
    #     <html lang="en">
    #     <head>
    #         <meta charset="UTF-8">
    #         <title>Dashboard</title>
    #     </head>
    #     <body>
    #         <h1>Dashboard</h1>
    #         <p>System is operational.</p>
    #     </body>
    #     </html>
    #     """

    #     resource = TextResourceContents(
    #         uri=AnyUrl("ui://dashboard"),
    #         mimeType=mime_type,
    #         text=html_document,
    #     )
    #     return EmbeddedResource(
    #         type="resource",
    #         resource=resource
    #         )
        # return CallToolResult(
        #     content=[TextContent(type="text", text="Dashboard loaded with image from Acontext.")],
        #     structuredContent={"uiResource": ui}
        # )
    
        # img = PILImage.open('/Users/kushaldevgun/Downloads/images/bar_chart.png')
        # img.save('/mnt/user-data/uploads/bar_chart.png')
        # sandboxed_path = "/mnt/user-data/uploads/bar_chart.png"
        # mime, _ = mimetypes.guess_type(sandboxed_path)

#    def show_interactive_demo(self) -> CallToolResult:
#         """Show an interactive demo with buttons that send intents."""
#         interactive_html = """
#         <div style="padding: 20px; font-family: Arial, sans-serif;">
#             <h2>Interactive Demo</h2>
#             <p>Click the buttons below to send different types of actions back to the parent:</p>
            
#             <div style="margin: 10px 0;">
#                 <button onclick="sendIntent('user_action', {type: 'button_click', id: 'demo'})" 
#                         style="background: #2563eb; color: white; padding: 8px 16px; border: none; border-radius: 4px; margin: 5px; cursor: pointer;">
#                     Send Intent
#                 </button>
#                 <button onclick="sendToolCall('get_data', {source: 'ui'})" 
#                         style="background: #059669; color: white; padding: 8px 16px; border: none; border-radius: 4px; margin: 5px; cursor: pointer;">
#                     Call Tool
#                 </button>
#             </div>
            
#             <div id="status" style="margin-top: 20px; padding: 10px; background: #f3f4f6; border-radius: 4px;">
#                 Ready - click a button to see the action
#             </div>
#         </div>
        
#         <script>
#             function sendIntent(intent, params) {
#                 const status = document.getElementById('status');
#                 status.innerHTML = `<strong>Intent sent:</strong> ${intent}<br><strong>Params:</strong> ${JSON.stringify(params)}`;
                
#                 if (window.parent) {
#                     window.parent.postMessage({
#                         type: 'intent',
#                         payload: { intent: intent, params: params }
#                     }, '*');
#                 }
#             }
            
#             function sendToolCall(toolName, params) {
#                 const status = document.getElementById('status');
#                 status.innerHTML = `<strong>Tool call:</strong> ${toolName}<br><strong>Params:</strong> ${JSON.stringify(params)}`;
                
#                 if (window.parent) {
#                     window.parent.postMessage({
#                         type: 'tool',
#                         payload: { toolName: toolName, params: params }
#                     }, '*');
#                 }
#             }
#         </script>
#         """
        
#         ui_resource = create_ui_resource({
#             "uri": "ui://demo/interactive",
#             "content": {
#                 "type": "rawHtml",
#                 "htmlString": interactive_html
#             },
#             "encoding": "text"
#         })
#         return [ui_resource]

# client = AcontextClient(api_key="sk-ac-HnRuhB0Z3i2xlrBAL26LN9ZUc9Wx2EHEhwGLNlr7BIk", )
            # disk = client.disks.create()
            # artifact = client.disks.artifacts.upsert(
            #     disk.id,
            #     file=FileUpload(filename="bar_chart_1.svg", content=png_bytes),
            #     file_path="/images/",
            #     meta={"kind": "chart"}
            # )

            # # 3) Ask for a public URL explicitly
            # result = client.disks.artifacts.get(
            #     disk.id,
            #     file_path="/images/",
            #     filename="bar_chart_1.svg",
            #     with_public_url=True
            # )
            # uri = result.public_url
            # await self.mcp.get_context().session.send_log_message("critical", f"Fetched image from Acontext with URI: {uri}")
            #img = PILImage.open('/Users/kushaldevgun/Downloads/images/bar_chart_1.png')
            # img.save('/mnt/user-data/uploads/bar_chart_1.png')
            # sandboxed_path = "/mnt/user-data/uploads/bar_chart_1.png"
            # mime, _ = mimetypes.guess_type(sandboxed_path)
   # def show_interactive_demo(self) -> list[UIResource]:
    #     """Show an interactive demo with buttons that send intents."""
    #     interactive_html = """
    #     <div style="padding: 20px; font-family: Arial, sans-serif;">
    #         <h2>Interactive Demo</h2>
    #         <p>Click the buttons below to send different types of actions back to the parent:</p>
            
    #         <div style="margin: 10px 0;">
    #             <button onclick="sendIntent('user_action', {type: 'button_click', id: 'demo'})" 
    #                     style="background: #2563eb; color: white; padding: 8px 16px; border: none; border-radius: 4px; margin: 5px; cursor: pointer;">
    #                 Send Intent
    #             </button>
    #             <button onclick="sendToolCall('get_data', {source: 'ui'})" 
    #                     style="background: #059669; color: white; padding: 8px 16px; border: none; border-radius: 4px; margin: 5px; cursor: pointer;">
    #                 Call Tool
    #             </button>
    #         </div>
            
    #         <div id="status" style="margin-top: 20px; padding: 10px; background: #f3f4f6; border-radius: 4px;">
    #             Ready - click a button to see the action
    #         </div>
    #     </div>
        
    #     <script>
    #         function sendIntent(intent, params) {
    #             const status = document.getElementById('status');
    #             status.innerHTML = `<strong>Intent sent:</strong> ${intent}<br><strong>Params:</strong> ${JSON.stringify(params)}`;
                
    #             if (window.parent) {
    #                 window.parent.postMessage({
    #                     type: 'intent',
    #                     payload: { intent: intent, params: params }
    #                 }, '*');
    #             }
    #         }
            
    #         function sendToolCall(toolName, params) {
    #             const status = document.getElementById('status');
    #             status.innerHTML = `<strong>Tool call:</strong> ${toolName}<br><strong>Params:</strong> ${JSON.stringify(params)}`;
                
    #             if (window.parent) {
    #                 window.parent.postMessage({
    #                     type: 'tool',
    #                     payload: { toolName: toolName, params: params }
    #                 }, '*');
    #             }
    #         }
    #     </script>
    #     """
        
    #     ui_resource = create_ui_resource({
    #         "uri": "ui://demo/interactive",
    #         "content": {
    #             "type": "rawHtml",
    #             "htmlString": interactive_html
    #         },
    #         "encoding": "text"
    #     })
    #     return [ui_resource]
        
    # async def plot_bar_chart(self,session_state: BarChartSessionState) -> Dict[str, Any] | CallToolResult:

    #     def decide_step(session_state: BarChartSessionState) -> str:
    #         has_table_name = bool(session_state.table_name)
    #         has_column_name = bool(session_state.column_name)
    #         if not has_table_name:
    #             return BarChartSteps.ASK_TABLE_NAME.value
    #         elif not has_column_name:
    #             return BarChartSteps.ASK_COLUMN.value
    #         else:
    #             return BarChartSteps.GENERATE_CHART.value

    #     session = BARCHARTSESSION.setdefault(session_state.session_id, session_state)
    #     if session_state.table_name is not None:
    #         session.table_name = session_state.table_name
    #     if session_state.column_name is not None:
    #         session.column_name = session_state.column_name
    #     #await self.mcp.get_context().session.send_log_message("critical", f"Current session state: {session}")
    #     session.step = decide_step(session)
        
    #     if session.step == BarChartSteps.ASK_TABLE_NAME.value:
    #         return {
    #             'status': 'ask_table_name',
    #             'message': 'Please provide the name of the table for which you want to generate the bar chart.'
    #         }
    #     elif session.step == BarChartSteps.ASK_COLUMN.value:
    #         result = PostgresHelperFxns(adapter=self.adapter).check_table_exists(session.table_name)  # Check if table exists, raise error if not
    #         if not result:
    #             BARCHARTSESSION.pop(session.session_id, None)  # Clear session on error
    #             return {
    #                 'status': 'error',
    #                 'message': f'Table "{session.table_name}" does not exist. Please check the table name and try again.'
    #             }
    #         return {
    #             'status': 'ask_column',
    #             'message': 'Please provide the column for which you want to generate the bar chart.'
    #         }
    #     elif session.step == BarChartSteps.GENERATE_CHART.value:
    #         column_data = PostgresHelperFxns(adapter=self.adapter).fetch_column_data(session.table_name, session.column_name)
    #         if not column_data:
    #             return {
    #                 'status': 'error',
    #                 'message': f'No data found for column "{session.column_name}" in table "{session.table_name}". Please check the table and its column name and try again.'
    #             }
            

    #         unique_values = [row[session.column_name] for row in column_data]
    #         counts = [row['count'] for row in column_data]
    #         # unique_values = np.unique(column_data)
    #         # counts = np.array([np.sum(column_data == val) for val in unique_values])    

    #         #Plotting the bar chart and saving it to a buffer
    #         try:
                
    #             plt.figure(figsize=(10, 6))
    #             plt.bar(unique_values, counts, color='blue')
    #             plt.xlabel(session.column_name, fontsize=12)
    #             plt.ylabel('Values', fontsize=12)
    #             plt.title('Bar Chart', fontsize=14)
    #             plt.tight_layout()
    #             path = f'/Users/kushaldevgun/Downloads/{session.session_id}_bar_chart.png'
    #             #plt.savefig(path, format = 'png')  # Save the chart as an image file

    #             buf = io.BytesIO()
    #             plt.savefig(buf, format='png', dpi=130)
    #             plt.close()  # Close the plot to free up memory
    #             buf.seek(0)
    #             b64 = base64.b64encode(buf.read()).decode()
    #             # Read the saved image and encode it in base64
    #             #b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
    #             # return {
    #             #     "content": [
    #             #         {"type": "text", "text": f"Bar Chart - {session.column_name}"},
    #             #         {"type": "image", "data": b64, "mimeType": "image/png"}
    #             #         ]
    #             #     }   
    #             return CallToolResult(
    #                 content=[
    #                     TextContent(type="text", text=f"Bar Chart - {session.column_name}"),
    #                     ImageContent(type="image", data=b64, mimeType="image/png"),
    #                     ],
    #                     isError=False
    #                     )
    #             return PlotRenderTool(mcp=self.mcp).render_plot({
    #                 "image_path": path,
    #                 "title": f"Bar Chart - {session.column_name}"
    #                 })

    #             real_path = os.path.realpath(path)

    #             ALLOWED_DIR = "/Users/kushaldevgun/Downloads"
    #             # Restrict directory access
    #             if not real_path.startswith(os.path.realpath(ALLOWED_DIR) + os.sep):
    #                 raise ValueError("Access denied: path not allowed")

    #             if not os.path.isfile(real_path):
    #                 raise ValueError("File not found")

    #             mime, _ = mimetypes.guess_type(real_path)
    #             if not mime or not mime.startswith("image/"):
    #                 raise ValueError("Not a valid image")

    #             with open(real_path, "rb") as f:
    #                 blob = f.read()

    #             if len(blob) > 1_000_000:
    #                 raise ValueError("Image too large (>1MB)")

    #             b64 = base64.b64encode(blob).decode("utf-8")
    #             if b64 is None:
    #                 raise ValueError("Failed to encode image to base64")
                
    #             BARCHARTSESSION.pop(session.session_id, None)
    #             return ImageContent(
    #                 type="image",
    #                 data=b64,
    #                 mimeType=mime
    #             )
    #         except Exception as e:
    #             logging.error(f"Error generating bar chart: {e}")
    #             raise ValueError("Failed to generate bar chart.")
    #     else:
    #         return {
    #             'status': 'error',
    #             'message': 'Invalid step in bar chart generation process.'
    #         }

    # async def plot_bar_chart(self, session_state: BarChartSessionState) -> CallToolResult:

    #     def text(msg: str, is_error: bool = False) -> CallToolResult:
    #         return CallToolResult(
    #             content=[TextContent(type="text", text=msg)],
    #             isError=is_error,
    #         )

    #     def decide_step(session_state: BarChartSessionState) -> str:
    #         has_table_name = bool(session_state.table_name)
    #         has_column_name = bool(session_state.column_name)
    #         if not has_table_name:
    #             return BarChartSteps.ASK_TABLE_NAME.value
    #         elif not has_column_name:
    #             return BarChartSteps.ASK_COLUMN.value
    #         else:
    #             return BarChartSteps.GENERATE_CHART.value

    #     session = BARCHARTSESSION.setdefault(session_state.session_id, session_state)
    #     if session_state.table_name is not None:
    #         session.table_name = session_state.table_name
    #     if session_state.column_name is not None:
    #         session.column_name = session_state.column_name

    #     session.step = decide_step(session)

    #     if session.step == BarChartSteps.ASK_TABLE_NAME.value:
    #         return text("Please provide the name of the table for which you want to generate the bar chart.")

    #     if session.step == BarChartSteps.ASK_COLUMN.value:
    #         ok = PostgresHelperFxns(adapter=self.adapter).check_table_exists(session.table_name)
    #         if not ok:
    #             BARCHARTSESSION.pop(session.session_id, None)
    #             return text(f'Table "{session.table_name}" does not exist. Please check the table name and try again.', is_error=True)
    #         return text("Please provide the column for which you want to generate the bar chart.")

    #     if session.step == BarChartSteps.GENERATE_CHART.value:
    #         column_data = PostgresHelperFxns(adapter=self.adapter).fetch_column_data(session.table_name, session.column_name)
    #         if not column_data:
    #             return text(f'No data found for column "{session.column_name}" in table "{session.table_name}".', is_error=True)

    #         unique_values = [row[session.column_name] for row in column_data]
    #         counts = [row["count"] for row in column_data]

    #         try:
    #             plt.figure(figsize=(10, 6))
    #             plt.bar(unique_values, counts)
    #             plt.xlabel(session.column_name, fontsize=12)
    #             plt.ylabel("Values", fontsize=12)
    #             plt.title("Bar Chart", fontsize=14)
    #             plt.tight_layout()

    #             buf = io.BytesIO()
    #             plt.savefig(buf, format="png", dpi=130)
    #             plt.close()

    #             b64 = base64.b64encode(buf.getvalue()).decode("utf-8")

    #             BARCHARTSESSION.pop(session.session_id, None)
    #             html = f"""
    #             <!doctype html>
    #             <html>
    #             <head>
    #                 <meta charset="utf-8" />
    #                 <meta name="viewport" content="width=device-width, initial-scale=1" />
    #                 <style>
    #                 body {{
    #                     margin: 0;
    #                     padding: 16px;
    #                     font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
    #                 }}
    #                 .wrap {{
    #                     display: flex;
    #                     flex-direction: column;
    #                     gap: 12px;
    #                 }}
    #                 img {{
    #                     width: 100%;
    #                     height: auto;
    #                     border: 1px solid rgba(0,0,0,0.12);
    #                     border-radius: 12px;
    #                 }}
    #                 h2 {{ margin: 0; font-size: 16px; }}
    #                 </style>
    #             </head>
    #             <body>
    #                 <div class="wrap">
    #                 <h2>Bar Chart - {session.column_name}</h2>
    #                 <img src="data:image/png;base64,{b64}" />
    #                 </div>
    #             </body>
    #             </html>
    #             """
    #             return CallToolResult(
    #                 content=[
    #                     {
    #                         "type": "image",
    #                         "resource": {
    #                             "uri": "ui://charts/app",
    #                             "mimeType": "text/html;profile=mcp-app",
    #                             "text": html,
    #         },
    #                     },
    #                     TextContent(type="text", text="Bar chart rendered."),
    #                     ],
    #                     isError=False
    #                     )
    #             # return CallToolResult(
    #             #     content=[TextContent(type="text", text="Bar chart rendered in panel.")],
    #             #     structuredContent={
    #             #         "kind": "plot",
    #             #         "title": f"Bar Chart - {session.column_name}",
    #             #         "mimeType": "image/png",
    #             #         "image_b64": b64,
    #             #     },
    #             #     isError=False
    #             #     )
    #         except Exception as e:
    #             logging.error(f"Error generating bar chart: {e}")
    #             return text("Failed to generate bar chart.", is_error=True)

    #     return text("Invalid step in bar chart generation process.", is_error=True)