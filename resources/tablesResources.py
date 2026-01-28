import json
import logging
from adapters.postgresAdapter import PostgresAdapter
from utils.config import Configuration

logger = logging.getLogger(__name__)

class TablesResources:
    def __init__(self):
        self.adapter = PostgresAdapter(config=Configuration.DB_CONFIG)

    def get_hrdataset_clean_records(self, limit: int = 5):
        query = f"SELECT * FROM hrdataset_clean LIMIT {limit};"
        return self.adapter.execute_query(query, (limit,))


def resources(mcp):
    res = TablesResources()

    # Use @mcp.resource(...) so FastMCP creates a Resource WITH a read() method internally.
    @mcp.resource("db://hrdataset_clean")
    def hrdataset_clean() -> str:
        """
        Read hrdataset_clean records as JSON string.
        """
        try:
            rows = res.get_hrdataset_clean_records(limit=5)
            return json.dumps(rows, default=str)
        except Exception as e:
            logger.exception("Failed to read resource db://hrdataset_clean")
            return json.dumps({"error": str(e)})
        return hrdataset_clean    

# import logging
# from adapters.postgresAdapter import PostgresAdapter
# from utils.config import Configuration
# from mcp.server.fastmcp.resources import Resource

# class TablesResources:
#     def __init__(self):
#         self.adapter = PostgresAdapter(config=Configuration.DB_CONFIG)

#     def get_hrdataset_clean_records(limit: int = 5) -> list:
#         """Fetch records from the hrdataset_clean table."""
#         adapter = PostgresAdapter(config=Configuration.DB_CONFIG)
#         query = f"SELECT * FROM hrdataset_clean LIMIT {limit};"
#         try:
#             records = adapter.execute_query(query, (limit,))
#             return records
#         except Exception as e:
#             logging.error(f"Failed to fetch records: {e}")
#             return []

# def register_resources(mcp):
#     my_resources = TablesResources()
    
#     resource = Resource(
#         my_resources.get_hrdataset_clean_records,
#         name="get_hrdataset_clean_records",
#         uri='db://hrdataset_clean',
#         description="Fetch records from the hrdataset_clean table",
#         mime_type="application/json"
#     )
#     # Register bound methods as MCP resources
#     mcp.add_resource(resource)

# # @Resource()