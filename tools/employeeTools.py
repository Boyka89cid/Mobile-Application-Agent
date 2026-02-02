# import logging, inspect
# from typing import List, Dict, Any, Optional
# from adapters.postgresAdapter import PostgresAdapter
# from utils.config import Configuration, ToolPrompts
# from mcp.server.fastmcp import FastMCP

# def register_employee_tools(mcp: FastMCP):
#     tools = EmployeeTools()
    
#     # Registration of Tools
#     mcp.add_tool(tools.get_employee_details, name="get_employee_details", description=ToolPrompts.get_employee_details)
#     mcp.add_tool(tools.search_employees, name="search_employees", description=ToolPrompts.search_employees)
#     mcp.add_tool(tools.create_employee, name="create_employee", description=ToolPrompts.create_employee)
#     mcp.add_tool(tools.delete_employee, name="delete_employee", description=ToolPrompts.delete_employee)

# class EmployeeTools:
#     def __init__(self):
#         self.adapter = PostgresAdapter(config=Configuration.DB_CONFIG)

#     # Get employee details by name, supports table targeting, needs to specify table if not default for some cases 
#     def get_employee_details(self, name: str, table_name: str = "hrdataset_clean") -> str:
#         query = f"SELECT employee_id, salary, tenure FROM {table_name} WHERE name = %s;"
#         try:
#             results = self.adapter.execute_query(query, (name,))
#             if not results:
#                 # Helpful error message tells the LLM IT looked in the wrong place
#                 return f"No results for '{name}' in table '{table_name}'. Did you mean a different table?"
            
#             if len(results) > 1:
#                 return f"Multiple employees found in {table_name}: {results}. Please provide an ID."
                
#             return f"Details from {table_name}: {results[0]}"
#         except Exception as e:
#             return f"Database error: {str(e)}"

#     # Search employees by name with limit, supports table targeting
#     def search_employees(self, query: str, limit: int = 5, table_name: str = "hrdataset_clean") -> str:
#         sql = f"SELECT name, employee_id FROM {table_name} WHERE name ILIKE %s LIMIT %s;"
#         try:
#             results = self.adapter.execute_query(sql, (f"%{query}%", limit))
#             return f"Search results from {table_name}: {results}"
#         except Exception as e:  
#             return f"Search failed: {e}"

#     # Create employee with validation and preview, supports table targeting
#     def create_employee(self, name: str, salary: float, tenure: int, table_name: str = "hrdataset_clean") -> Dict[str, Any]:
#         if salary < 0 or tenure < 0: # Validation Step
#             return {"status": "error", "message": "Salary and tenure must be positive."}
        
#         preview = {"name": name, "salary": salary, "tenure": tenure, "target": table_name}
#         query = f"INSERT INTO {table_name} (name, salary, tenure) VALUES (%s, %s, %s) RETURNING employee_id;"
        
#         try:
#             result = self.adapter.execute_query(query, (name, salary, tenure))
#             return {
#                 "status": "success",
#                 "preview": preview,
#                 "message": f"Added to {table_name} with ID: {result[0]['employee_id']}"
#             }
#         except Exception as e:
#             return {"status": "error", "message": str(e)}

#     # Delete employee by name, handling duplicates and table targeting, only works with employee_id if duplicates exist
#     def delete_employee(self, name: str, employee_id: Optional[int] = None, table_name: str = "hrdataset_clean") -> str:
#         if not employee_id:
#             dup_check = f"SELECT employee_id FROM {table_name} WHERE name = %s;"
#             duplicates = self.adapter.execute_query(dup_check, (name,))
            
#             if len(duplicates) > 1:
#                 return f"Multiple '{name}' found in {table_name}: {duplicates}. Provide an ID to delete."
#             elif not duplicates:
#                 return f"No one named '{name}' in {table_name}."
#             employee_id = duplicates[0]['employee_id']

#         query = f"DELETE FROM {table_name} WHERE employee_id = %s;"
#         try:
#             self.adapter.execute_query(query, (employee_id,))
#             return f"Deleted {name} (ID: {employee_id}) from {table_name}."
#         except Exception as e:
#             return f"Error deleting from {table_name}: {e}"