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
