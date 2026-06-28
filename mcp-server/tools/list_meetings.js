/**
 * Tool metadata and input schema definition for list_meetings.
 * The implementation (database queries) is deferred to task T11.4.
 */

export const name = "list_meetings";
export const description =
  "Lists meetings with optional pagination (limit, offset) and status filters.";

export const inputSchema = {
  type: "object",
  properties: {
    limit: {
      type: "integer",
      description: "Number of records to return (default 10, max 100)",
      minimum: 1,
      maximum: 100,
    },
    offset: {
      type: "integer",
      description: "Number of records to skip (default 0)",
      minimum: 0,
    },
    status: {
      type: "string",
      enum: ["pending", "processing", "completed", "failed"],
      description: "Filter meetings by status",
    },
  },
};

/**
 * Stub execution handler for list_meetings.
 *
 * @param {object} args - Tool arguments.
 * @returns {Promise<object>}
 */
export async function handler(args) {
  console.error("list_meetings tool invoked with args:", args);
  return {
    content: [
      {
        type: "text",
        text: "list_meetings tool stub: logic will be implemented in T11.4",
      },
    ],
  };
}
