import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";

// Import tool definitions
import * as listMeetings from "./tools/list_meetings.js";
import * as searchTranscripts from "./tools/search_transcripts.js";
import { closePool } from "./database.js";

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

  // 1. Tool Registration Handler (Exposes metadata and input schemas to clients)
  server.setRequestHandler(ListToolsRequestSchema, async () => {
    console.error("Listing registered tools for MCP client...");
    return {
      tools: [
        {
          name: listMeetings.name,
          description: listMeetings.description,
          inputSchema: listMeetings.inputSchema,
        },
        {
          name: searchTranscripts.name,
          description: searchTranscripts.description,
          inputSchema: searchTranscripts.inputSchema,
        },
      ],
    };
  });

  // 2. Tool Execution Handler (Routes incoming calls to the respective stub handler)
  server.setRequestHandler(CallToolRequestSchema, async (request) => {
    const { name, arguments: args } = request.params;
    console.error(`Received request to call tool: ${name}`);

    switch (name) {
      case listMeetings.name:
        return await listMeetings.handler(args);
      case searchTranscripts.name:
        return await searchTranscripts.handler(args);
      default:
        console.error(`Tool not found: ${name}`);
        throw new Error(`Tool not found: ${name}`);
    }
  });

  // Set up basic request error handling
  server.onerror = (error) => {
    console.error("MCP Server Error:", error);
  };

  // Graceful shutdown handling
  const shutdown = async () => {
    console.error("Shutting down MCP server...");
    try {
      await closePool();
    } catch (err) {
      console.error("Error closing database pool during shutdown:", err.message);
    }
    process.exit(0);
  };

  process.on("SIGINT", shutdown);
  process.on("SIGTERM", shutdown);

  // Connect using standard input/output transport
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("MCP server connected to stdio transport.");
}

main().catch((error) => {
  console.error("Fatal error starting MCP server:", error);
  process.exit(1);
});
