from mcp.server.fastmcp import FastMCP
from mcp.types import ImageContent
import inspect, logging, matplotlib.pyplot as plt, base64, os, mimetypes
import numpy as np
from typing import Dict, Any
from tools.figureOchestrator.figToolDescriptions import FigToolPrompts
from adapters.postgresAdapter import PostgresAdapter
from tools.queryOrchestrator.postgresHelperFxns import PostgresHelperFxns
from utils.config import Configuration
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
    
    def plot_bar_chart(self,session_state: BarChartSessionState) -> Dict[str, Any] | ImageContent:

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

            # Plotting the bar chart and saving it to a buffer
            try:
                plt.figure(figsize=(10, 6))
                plt.bar(unique_values, counts, color='purple')
                plt.xlabel(session.column_name, fontsize=12)
                plt.ylabel('Values', fontsize=12)
                plt.title('Bar Chart', fontsize=14)
                plt.tight_layout()
                path = f'/Users/luisdhernandez/Downloads/{session.session_id}_bar_chart.png'
                plt.savefig(path, format = 'png')  # Save the chart as an image file
                plt.close()  # Close the plot to free up memory
                # Read the saved image and encode it in base64
                real_path = os.path.realpath(path)

                ALLOWED_DIR = "/Users/luisdhernandez/Downloads"
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

    def plot_pie_chart(self, session_state: PieChartSessionState) -> Dict[str, Any] | ImageContent:
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
                plt.figure(figsize=(8, 8))
                plt.pie(sizes, labels=labels, autopct='%1.1 f%%', startangle=140)
                plt.title(f'Distribution of {session.category_column} in {session.table_name}')
                
                path = f'/Users/luisdhernandez/Downloads/{session.session_id}_pie_chart.png'
                plt.savefig(path, format='png')
                plt.close()

                # Reuse your existing base64 encoding logic
                with open(path, "rb") as f:
                    b64 = base64.b64encode(f.read()).decode("utf-8")
                
                PIECHARTSESSION.pop(session.session_id, None)
                return ImageContent(type="image", data=b64, mimeType="image/png")
            except Exception as e:
                logging.error(f"Pie chart error: {e}")
                return {"status": "error", "message": "Failed to generate pie chart."}
    
    def plot_histogram(self, session_state: HistogramSessionState) -> Dict[str, Any] | ImageContent:
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
            return {"status": "ask_table_name", "message": "Which table contains the numeric data for the histogram?"}

        elif session.step == HistogramSteps.ASK_NUMERIC_COLUMN.value:
            if not PostgresHelperFxns(self.adapter).check_table_exists(session.table_name):
                HISTOGRAMSESSION.pop(session.session_id, None)
                return {"status": "error", "message": f"Table '{session.table_name}' not found."}
            return {"status": "ask_column", "message": "Which numeric column would you like to analyze?"}

        elif session.step == HistogramSteps.GENERATE_HISTOGRAM.value:
            # Fetch raw data for the specific column
            query = f'SELECT "{session.numeric_column}" FROM "{session.table_name}" WHERE "{session.numeric_column}" IS NOT NULL;'
            results = self.adapter.execute_query(query)
            
            if not results:
                return {"status": "error", "message": "No numeric data found for this column."}

            data = [row[session.numeric_column] for row in results]

            try:
                plt.figure(figsize=(10, 6))
                plt.hist(data, bins=session.bins, color='skyblue', edgecolor='black')
                plt.title(f'Frequency Distribution of {session.numeric_column}')
                plt.xlabel(session.numeric_column)
                plt.ylabel('Frequency')
                
                path = f'/Users/luisdhernandez/Downloads/{session.session_id}_histogram.png'
                plt.savefig(path, format='png')
                plt.close()

                # Encode to base64 using established project patterns
                with open(path, "rb") as f:
                    b64 = base64.b64encode(f.read()).decode("utf-8")
                
                HISTOGRAMSESSION.pop(session.session_id, None)
                return ImageContent(type="image", data=b64, mimeType="image/png")
            except Exception as e:
                logging.error(f"Histogram error: {e}")
                return {"status": "error", "message": "Failed to generate histogram."}