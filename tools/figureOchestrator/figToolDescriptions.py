class FigToolPrompts:
    RULES = '''
    - You can skip a single or multiple steps if you already have the required information. For example, if you already have the table_type, you can skip the ask_table_type step. However, you cannot skip a step or steps if the required information is missing.
    - Respond ONLY with a tool call.
    - Do NOT include any natural-language explanation before the tool call.
    - After the tool returns, you may present exactly the tool's message verbatim.'''
      
    plot_bar_chart_workflow = f'''
    WORKFLOW: plot_bar_chart (state machine)
    State fields:
    - session_id: string (required)
    - step: enum[ ask_table_name, ask_column, generate_chart]
    - table_name: string
    - column_name: string
    {RULES}
    1) ask user for table_name if not provided.
    2) ask user for column_name if not provided.
    3) call generate_chart ONLY if table_name and column_name are non-null.
    If any required field is missing, move back to the appropriate ask_* step.
    '''
    plot_bar_chart = f"Orchestrate the process of generating a bar chart based on user input.\n {plot_bar_chart_workflow}"

    plot_pie_chart_workflow = f'''
    WORKFLOW: plot_pie_chart (state machine)
    State fields:
    - session_id: string (required)
    - table_name: string
    - category_column: string
    {RULES}
    1) Ask for table_name if not provided.
    2) Ask for category_column if not provided.
    3) Generate and return a pie chart showing the percentage distribution.
    '''
    plot_pie_chart = f"Generate a pie chart distribution for a specific column.\n {plot_pie_chart_workflow}"

    plot_histogram_workflow = f'''
    WORKFLOW: plot_histogram (state machine)
    State fields:
    - session_id: string (required)
    - table_name: string
    - numeric_column: string
    - bins: integer (optional, default 10)
    {RULES}
    1) Ask for table_name if not provided.
    2) Ask for numeric_column (e.g., salary, age) if not provided.
    3) Ask for number of bins if the user wants custom granularity.
    4) Generate and return a histogram image.
    '''
    plot_histogram = f"Generate a histogram to show the frequency distribution of numeric data.\n {plot_histogram_workflow}"