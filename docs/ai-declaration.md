# AI Declaration Document

## Proposition for the start of the project:

For our project, we will try to omit the usage of AI tools as long as possible since we are providing context to AI thought prompting to build the application for us. So, in our case, using AI would not be very beneficial and would be used only to a limited extent. We expect to use ChatGPT, which would be verified by checking various prompts we have written, and various tools don't exactly match their output, rather than being based on human intelligence.
Although we used AI during the project in different scenarios,
- Getting familiar with the MCP server and its basic usage cases.
- Getting hints on different collaboration work done by others to find out the limitations of their work and the uniqueness of our technique.
- While debugging SQL queries with orchestration, we often used AI to help us resolve the issue.
- Also, we used AI to check our project file structure

--- 

# Final Engineering Reflection & AI Usage Log:

## What We Built

For this project, our two-person team designed and implemented a Model Context Protocol
(MCP) server that bridges Claude Desktop with a PostgreSQL-backed HR database. The
system enables natural language interaction with employee records, department structures,
and HR workflows directly through Claude's chat interface — eliminating the need for manual
SQL queries or separate database tooling for routine tasks.

The stack consisted of a custom MCP server written to expose HR database operations as
callable tools, a PostgreSQL database that stored and managed all HR data, and DBeaver as
our visual database management environment for schema design, inspection, and query
validation. Claude Desktop served as the front-end interface, allowing users to query, update,
and retrieve HR information conversationally. Together, these components formed a cohesive
system where a user could, for example, ask Claude to pull all employees in a specific
department or update a record — and have that action execute against a live database.

##  Major Technical Challenges

The most significant challenge we encountered was configuring the MCP protocol layer
correctly. Getting the MCP server to register, expose, and execute tools reliably within Claude
Desktop required careful attention to the protocol specification — particularly around tool
definitions, input schema validation, and how Claude interprets available tools at runtime.
Early iterations resulted in tools either not appearing in Claude's context or failing silently due
to schema mismatches.

Establishing a stable connection between the MCP server and PostgreSQL also presented
hurdles, especially around authentication configuration and ensuring the server handled
connection pooling gracefully under repeated queries. DBeaver proved invaluable here, giving
us a clear visual window into the database state to catch issues that were otherwise difficult to
surface through the MCP interface alone.

## How AI Was Used and Verified

AI — primarily Claude — played an active role throughout the development process. We used
it to scaffold MCP server boilerplate, generate PostgreSQL schema definitions for common
HR data models, draft tool definitions with proper input/output schemas, and troubleshoot
protocol-level errors when integration issues arose. Claude also assisted in writing and
refining SQL queries for specific HR operations.

Verification was multi-layered. All AI-generated SQL queries and schema changes were
reviewed visually in DBeaver before being applied, allowing us to confirm correctness against
the actual database structure. We ran integration tests to validate that MCP tool calls
produced the expected database results end-to-end. Additionally, both team members
peer-reviewed AI-generated code before merging, ensuring that no output was accepted
without a human reading and understanding it first. This combination of manual inspection,
live testing, and peer review gave us confidence in the reliability of AI-assisted work.

## What We'd Improve Next

The most important area for improvement is error handling throughout the system. Currently,
when a tool call fails — whether due to a malformed query, a database constraint violation, or
a connection issue — the error surface back to Claude is minimal. This makes it difficult for
the model to reason about what went wrong or suggest a corrective action to the user.
In a future iteration, we would implement structured error responses from the MCP server that
categorize failure types (e.g., validation error, permission denied, record not found) and
include actionable context. This would allow Claude to respond more intelligently to failures
and improve the overall user experience significantly. We would also add input sanitization at
the MCP layer to prevent malformed requests from ever reaching the database, and introduce
logging to make debugging faster and more systematic.