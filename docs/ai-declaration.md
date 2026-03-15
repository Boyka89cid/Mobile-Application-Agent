# AI Declaration Document

## Proposition for the start of the project:

For our project, we will try to omit the usage of AI tools as long as possible since we are providing context to AI thought prompting to build the application for us. So, in our case, using AI would not be very beneficial and would be used only to a limited extent. We expect to use ChatGPT, which would be verified by checking various prompts we have written, and various tools don't exactly match their output, rather than being based on human intelligence.
Although we used AI during the project in different scenarios,
- Getting familiar with the MCP server and its basic usage cases.
- Getting hints on different collaboration work done by others to find out the limitations of their work and the uniqueness of our technique.
- While debugging SQL queries with orchestration, we often used AI to help us resolve the issue.
- Also, we used AI to check our project file structure

--- 

# Final AI Usage Log:

## Week 2

### Task
Generate initial PostgreSQL schema for HR database

### Prompt / AI Interaction
Asked Claude to design a relational schema for an HR system covering employees, departments, roles, and payroll, including foreign key relationships and recommended indexes.

### Output
Claude produced a complete set of CREATE TABLE statements with appropriate constraints, foreign keys, and indexing suggestions for common query patterns.

### Verification
Schema was manually reviewed by both team members and executed in a test PostgreSQL instance via DBeaver, where table structures and relationships were visually inspected.

## Week 3

### Task
Draft MCP server boilerplate and project structure

### Prompt / AI Interaction
Asked Claude to scaffold a Python-based MCP server using the MCP SDK, including stdio transport setup and basic tool registration patterns.

### Output
Claude generated a working server skeleton with a main entry point, tool registration hooks, and a sample tool definition to use as a reference.

### Verification
Server was run locally and connected to Claude Desktop to confirm it appeared in the tools list and responded to a basic ping-style call.

## Week 4

### Task
Define MCP tool schemas for core HR operations

### Prompt / AI Interaction
Asked Claude to write JSON schema definitions for four MCP tools: get_employee, list_department, search_by_role, and update_salary, including input types, required fields, and descriptions.

### Output 
Claude returned fully structured tool definitions with typed parameters, optional field handling, and human-readable descriptions suitable for Claude Desktop display.

### Verification
Each tool schema was peer reviewed by the teammate and tested end-to-end from Claude Desktop, checking that inputs were correctly passed to the server.

## Week 5

### Task
Write parameterized SQL queries for common HR lookups

### Prompt / AI Interaction
Asked Claude to produce SQL queries for filtering employees by department, hire date range, and salary band, using parameterized inputs to prevent injection.

### Output
Claude returned five queries with parameter placeholders, along with notes on NULL handling and edge cases for empty result sets.

### Verification
All queries were executed directly in DBeaver against the test database with both valid and edge-case inputs to confirm correctness and safety.

## Week 6

### Task
Debug MCP tool returning empty results unexpectedly

### Prompt / AI Interaction
Described the issue to Claude — a tool call that should return employee records was returning an empty list despite matching data existing in the database.

### Output
Claude identified a missing NULL check in the WHERE clause as the most likely cause and suggested a corrected query with COALESCE handling.

### Verification
The bug was reproduced in DBeaver to confirm the diagnosis, the fix was applied, and the full integration test was re-run to verify the tool returned correct results.

## Week 7

### Task
Generate seed data for testing the HR database

### Prompt / AI Interaction
Asked Claude to generate INSERT statements for 30 realistic fake employees spread across 5 departments, with varied roles, salaries, and hire dates.

### Output
Claude produced a full SQL seed file with believable names, job titles, salary figures, and hire dates spanning several years.

### Verification
Seed data was loaded into PostgreSQL via DBeaver and rows were visually inspected to ensure diversity and referential integrity across tables.

## Week 8

### Task
Review MCP tool definitions for completeness and edge cases

### Prompt / AI Interaction
Asked Claude to audit the existing tool schemas and flag any missing optional fields, ambiguous descriptions, or inputs that lacked validation constraints.

### Output
Claude identified two missing optional fields and recommended adding enum constraints on role and department inputs to reduce invalid calls.

### Verification
Suggestions were cross-referenced against the MCP specification documentation and applied after both team members agreed the changes were appropriate.

## Week 9

### Task
Draft repository README and project documentation

### Prompt / AI Interaction
Asked Claude to write a README covering project overview, setup instructions, environment variable configuration, and a description of each available MCP tool.

### Output
Claude produced a full markdown README with installation steps, a prerequisites section, environment variable table, and usage examples for each tool.

### Verification
The README was reviewed by the teammate against the actual project setup to confirm all instructions were accurate and reproducible in a fresh environment.


All AI-generated outputs were treated as drafts and verified by at least one team member before being incorporated into the project.
