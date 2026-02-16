from dataclasses import dataclass
from typing import Dict, Any
from tools.figureOchestrator.figSessionSteps import BarChartSteps

@dataclass
class BarChartSessionState:
    session_id: str
    step: str = BarChartSteps.ASK_TABLE_NAME.value
    table_name: str = ''
    column_name: str = ''