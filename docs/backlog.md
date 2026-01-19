## PROBLEM STATEMENT

The end user for this project is any organization that wants to manage employee databases automatically, without knowledge of the coding required to support the databases, or without manually doing it on the dashboard. 

Our team is interested in using AI to make HR tasks easier and less time consuming for organizations. A lot of employee management systems are complicated and require technical knowledge or manual work through dashboards. Even though LLMs are powerful, they usually give very general answers and can’t safely interact with company databases on their own. We want to build this AI agent that works on top of existing models and uses tools to manage employee data in a more controlled and personalized way. 

This software helps by letting users manage employee information through simple natural language instead of complex dashboards or technical tools. The AI agent handles repetitive HR tasks automatically by using structured tools and company specific context, reducing manual work and errors. The system makes it safer for organizations to let AI interact directly with their data.
## Backlog Issues

### PROBLEM STATEMENT
The end user for this project is any organization that wants to manage employee databases automatically, without knowledge of the coding required to support the databases, or without manually doing it on the dashboard.
Our team is interested in using AI to make HR tasks easier and less time-consuming for organizations. Many employee management systems are complicated and require technical knowledge or manual work via dashboards. Even though LLMs are powerful, they usually give very general answers and cannot safely interact with company databases on their own. We want to build an AI agent that runs on top of existing models and uses tools to manage employee data in a more controlled, personalized way.
This Agent helps users manage employee information through simple, natural language rather than complex dashboards or technical tools. The AI agent automates repetitive HR tasks using structured tools and company-specific context, reducing manual work and errors. The system makes it safer for organizations to let AI interact directly with their data.

### Priority — CRUD Tools and basic visualization for HR Data Model & Ingestion
- Use a public or synthetic dataset and define an HR data schema (role, department, location, tenure, salary range). Load and normalize HR-related data from public CSV/JSON files into a local data store for read-only analysis first. Below is the list of tools we need to cover on the MCP server: **(Week 2)**
    - get_employee_details(): Get employee id, salary, tenure by name. The tool must validate and check for duplicate names and get data back appropriately.
    - search_employees(): search employees with a given query and limit
    - create_employee() & create_employee_preview(): This should create an employee, validate its fields, and preview the created employee

    - delete_employee(): This tool should delete employees according to name. The tool should fetch people with multiple names correctly and differentiate them accordingly.
    - list_team_members(): Get team members of an employee
    - get_manager_chain(): get the chain for management for an employee 
    - headcount_by_department() & headcount_by_location(): enable search by department and location.

    **Note**: Add appropriate prompts (mandatory for guidance) while providing context to LLM.
- Add basic data updation, validation, and deduplication tools. Below is the list of tools we need to cover on the MCP server: **(Week 3 and Week 4)**
    - update_employee(): This tool could help update role, location, project assigned, working years, leaves, and salary
    - validate_employee(): This tool should validate whether the employee information currently written is correct or not. Checked for duplication.
    - validate_employee_schema(): Checks required fields, enum values, and numeric ranges (salary, tenure, leaves)
    - get_boxplot_stats() & get_histogram_stats(): draw basic box_plots that's dosen't all the data. The phg/jgep file will be rendered by Claude. You can also check out other [drawable plots](https://medium.com/firebird-technologies/building-an-agent-for-data-visualization-plotly-39310034c4e9) and [check already existing ones](,https://github.com/antvis/mcp-server-chart).

## Out of Scope for Prototype Sprint
- Direct CRUD operations on real employee databases
- Integration with proprietary HR systems
- Real-time data streaming or alerting
- Authentication and role-based access control
