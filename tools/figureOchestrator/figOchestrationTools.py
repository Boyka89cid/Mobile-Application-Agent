from mcp.server.fastmcp import FastMCP
from mcp.types import ImageContent
import inspect, logging, matplotlib.pyplot as plt, base64, os, mimetypes
import numpy as np
from typing import Dict, Any
from tools.figureOchestrator.figToolDescriptions import FigToolPrompts
from tools.figureOchestrator.figSessionDataClasses import BarChartSessionState
from tools.figureOchestrator.figSessionSteps import BarChartSteps
from adapters.postgresAdapter import PostgresAdapter
from tools.queryOrchestrator.postgresHelperFxns import PostgresHelperFxns
from utils.config import Configuration

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

class FigOchestrationTools:
    def __init__(self, mcp: FastMCP, adapter: PostgresAdapter):
        self.mcp = mcp
        self.adapter = adapter
    
    async def plot_bar_chart(self,session_state: BarChartSessionState) -> Dict[str, Any] | ImageContent:

        def decide_step(session_state: BarChartSessionState) -> str:
            has_table_name = bool(session_state.table_name)
            has_column_name = bool(session_state.column_name)
            if not has_table_name:
                return BarChartSteps.ASK_TABLE_NAME.value
            elif not has_column_name:
                return BarChartSteps.ASK_COLUMN.value
            else:
                return BarChartSteps.GENERATE_CHART.value

        session = BARCHARTSESSION.setdefault(session_state.session_id, session_state)
        if session_state.table_name is not None:
            session.table_name = session_state.table_name
        if session_state.column_name is not None:
            session.column_name = session_state.column_name
        #await self.mcp.get_context().session.send_log_message("critical", f"Current session state: {session}")
        session.step = decide_step(session)
        
        if session.step == BarChartSteps.ASK_TABLE_NAME.value:
            return {
                'status': 'ask_table_name',
                'message': 'Please provide the name of the table for which you want to generate the bar chart.'
            }
        elif session.step == BarChartSteps.ASK_COLUMN.value:
            result = PostgresHelperFxns(adapter=self.adapter).check_table_exists(session.table_name)  # Check if table exists, raise error if not
            if not result:
                BARCHARTSESSION.pop(session.session_id, None)  # Clear session on error
                return {
                    'status': 'error',
                    'message': f'Table "{session.table_name}" does not exist. Please check the table name and try again.'
                }
            return {
                'status': 'ask_column',
                'message': 'Please provide the column for which you want to generate the bar chart.'
            }
        
        elif session.step == BarChartSteps.GENERATE_CHART.value:
            column_data = PostgresHelperFxns(adapter=self.adapter).fetch_column_data(session.table_name, session.column_name)
            if not column_data:
                return {
                    'status': 'error',
                    'message': f'No data found for column "{session.column_name}" in table "{session.table_name}". Please check the table and its column name and try again.'
                }
            

            unique_values = [row[session.column_name] for row in column_data]
            counts = [row['count'] for row in column_data]
            # unique_values = np.unique(column_data)
            # counts = np.array([np.sum(column_data == val) for val in unique_values])    

            #Plotting the bar chart and saving it to a buffer
            try:
                plt.figure(figsize=(10, 6))
                plt.bar(unique_values, counts, color='blue')
                plt.xlabel(session.column_name, fontsize=12)
                plt.ylabel('Values', fontsize=12)
                plt.title('Bar Chart', fontsize=14)
                plt.tight_layout()
                path = f'/Users/kushaldevgun/Downloads/{session.session_id}_bar_chart.png'
                plt.savefig(path, format = 'png')  # Save the chart as an image file
                plt.close()  # Close the plot to free up memory
                # Read the saved image and encode it in base64
                real_path = os.path.realpath(path)

                ALLOWED_DIR = "/Users/kushaldevgun/Downloads"
                # Restrict directory access
                if not real_path.startswith(os.path.realpath(ALLOWED_DIR) + os.sep):
                    raise ValueError("Access denied: path not allowed")

                if not os.path.isfile(real_path):
                    raise ValueError("File not found")

                mime, _ = mimetypes.guess_type(real_path)
                if not mime or not mime.startswith("image/"):
                    raise ValueError("Not a valid image")

                with open(real_path, "rb") as f:
                    blob = f.read()

                if len(blob) > 1_000_000:
                    raise ValueError("Image too large (>1MB)")

                b64 = base64.b64encode(blob).decode("utf-8")
                if b64 is None:
                    raise ValueError("Failed to encode image to base64")
                
                BARCHARTSESSION.pop(session.session_id, None)
                return ImageContent(
                    type="image",
                    data=b64,
                    mimeType=mime
                )
            except Exception as e:
                logging.error(f"Error generating bar chart: {e}")
                raise ValueError("Failed to generate bar chart.")
        else:
            return {
                'status': 'error',
                'message': 'Invalid step in bar chart generation process.'
            }

    