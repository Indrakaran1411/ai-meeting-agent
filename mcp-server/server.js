import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";

async function main() {
  console.error("Starting MCP server...");

  // Instantiate the server with metadata and capabilities
  const server = new Server(
    {
      name: "meeting-agent-mcp",
      version: "1.0.0",
    },
    {
      capabilities: {
        tools: {},
      },
    }
  );

  // Set up basic request error handling
  server.onerror = (error) => {
    console.error("MCP Server Error:", error);
  };

  // Graceful shutdown handling
  process.on("SIGINT", async () => {
    console.error("Shutting down MCP server...");
    process.exit(0);
  });

  // Connect using standard input/output transport
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("MCP server connected to stdio transport.");
}

main().catch((error) => {
  console.error("Fatal error starting MCP server:", error);
  process.exit(1);
});
