import json
from adapters.postgresAdapter import PostgresAdapter
from utils.config import Configuration
from mcp.server.fastmcp import FastMCP

class TablesResources:
    def __init__(self, mcp: FastMCP):
        self.mcp = mcp
        self.adapter = PostgresAdapter(config=Configuration.DB_CONFIG)

    def get_hrdataset_records(self, limit: int = 5):
        query = f"SELECT * FROM hrdataset LIMIT {limit};"
        return self.adapter.execute_query(query, (limit,))


def resources(mcp: FastMCP):
    res = TablesResources(mcp=mcp)

    # Use @mcp.resource(...) so FastMCP creates a Resource WITH a read() method internally.
    @mcp.resource("db://hrdataset")
    def hrdataset() -> str:
        """
        Read hrdataset records as JSON string.
        """
        try:
            rows = res.get_hrdataset_records(limit=5)
            return json.dumps(rows, default=str)
        except Exception as e:
            mcp.get_context().session.send_log_message("error", f"Failed to read resource db://hrdataset: {e}")
            #logger.exception("Failed to read resource db://hrdataset")
            return json.dumps({"error": str(e)}) 