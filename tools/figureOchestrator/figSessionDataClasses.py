from dataclasses import dataclass
from typing import Dict, Any
from tools.figureOchestrator.figSessionSteps import BarChartSteps, PieChartSteps, HistogramSteps

@dataclass
class BarChartSessionState:
    session_id: str
    step: str = BarChartSteps.ASK_TABLE_NAME.value
    table_name: str = ''
    column_name: str = ''

@dataclass
class PieChartSessionState:
    session_id: str
    step: str = PieChartSteps.ASK_TABLE_NAME.value
    table_name: str = ''
    category_column: str = ''

@dataclass
class HistogramSessionState:
    session_id: str
    step: str = HistogramSteps.ASK_TABLE_NAME.value
    table_name: str = ''
    numeric_column: str = ''
    bins: int = 10  # Default to 10 bins