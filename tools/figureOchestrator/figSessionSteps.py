from enum import Enum

class BarChartSteps(Enum):
    ASK_TABLE_NAME = "ask_table_name"
    ASK_COLUMN = "ask_column"
    GENERATE_CHART = "generate_chart"

class PieChartSteps(Enum):
    ASK_TABLE_NAME = "ask_table_name"
    ASK_CATEGORY_COLUMN = "ask_category_column"
    GENERATE_PIE_CHART = "generate_pie_chart"

class HistogramSteps(Enum):
    ASK_TABLE_NAME = "ask_table_name"
    ASK_NUMERIC_COLUMN = "ask_numeric_column"
    ASK_BINS = "ask_bins"
    GENERATE_HISTOGRAM = "generate_histogram"