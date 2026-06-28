/**
 * Tool metadata and input schema definition for search_transcripts.
 * The implementation (database queries) is deferred to task T11.4.
 */

export const name = "search_transcripts";
export const description =
  "Searches transcript segments using case-insensitive keyword query matching, returning speaker, content, timestamps, and meeting titles.";

export const inputSchema = {
  type: "object",
  properties: {
    query: {
      type: "string",
      description: "Search term or keyword to match in transcript content",
    },
    limit: {
      type: "integer",
      description: "Maximum number of matching segments to return (default 10, max 100)",
      minimum: 1,
      maximum: 100,
    },
  },
  required: ["query"],
};

/**
 * Stub execution handler for search_transcripts.
 *
 * @param {object} args - Tool arguments.
 * @returns {Promise<object>}
 */
export async function handler(args) {
  console.error("search_transcripts tool invoked with args:", args);
  return {
    content: [
      {
        type: "text",
        text: "search_transcripts tool stub: logic will be implemented in T11.4",
      },
    ],
  };
}
