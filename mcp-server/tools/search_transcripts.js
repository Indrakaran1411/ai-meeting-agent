import { query } from "../database.js";

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
 * Execution handler for search_transcripts.
 * Validates inputs, queries PostgreSQL database using parameterized SQL, and formats output.
 *
 * @param {object} args - Tool arguments.
 * @returns {Promise<object>}
 */
export async function handler(args) {
  console.error("search_transcripts tool invoked with args:", args);

  const rawQuery = args.query;
  const limit = args.limit !== undefined ? args.limit : 10;

  // 1. Input Validation
  if (rawQuery === undefined || rawQuery === null) {
    return {
      content: [{ type: "text", text: "Error: 'query' parameter is required." }],
      isError: true,
    };
  }

  if (typeof rawQuery !== "string") {
    return {
      content: [{ type: "text", text: "Error: 'query' parameter must be a string." }],
      isError: true,
    };
  }

  const queryStr = rawQuery.trim();
  if (queryStr === "") {
    return {
      content: [{ type: "text", text: "Error: 'query' parameter cannot be empty or whitespace only." }],
      isError: true,
    };
  }

  if (typeof limit !== "number" || !Number.isInteger(limit) || limit < 1 || limit > 100) {
    return {
      content: [{ type: "text", text: `Error: 'limit' must be an integer between 1 and 100. Got: ${limit}` }],
      isError: true,
    };
  }

  // 2. Database Execution using parameterized SQL
  try {
    const sql = `
      SELECT
          t.meeting_id,
          m.title AS meeting_title,
          t.speaker,
          t.start_time AS timestamp_start,
          t.end_time AS timestamp_end,
          t.content
      FROM transcripts t
      JOIN meetings m ON t.meeting_id = m.id
      WHERE t.content ILIKE $1
      ORDER BY m.created_at DESC, t.segment_index ASC
      LIMIT $2;
    `;
    const params = [`%${queryStr}%`, limit];
    const res = await query(sql, params);

    // 3. Output Formatting
    if (res.rows.length === 0) {
      return {
        content: [
          {
            type: "text",
            text: `No transcript segments matched the search query: "${queryStr}"`,
          },
        ],
      };
    }

    const formattedLines = res.rows.map((row) => {
      const speaker = row.speaker || "Unknown";
      const startSec = row.timestamp_start !== null ? `${row.timestamp_start}s` : "0s";
      const endSec = row.timestamp_end !== null ? `${row.timestamp_end}s` : "0s";
      
      return `Meeting: ${row.meeting_title} (ID: ${row.meeting_id})
Speaker: ${speaker}
Timestamp: ${startSec} - ${endSec}
Transcript: ${row.content}`;
    });

    const formattedText = formattedLines.join("\n\n---\n\n");

    return {
      content: [
        {
          type: "text",
          text: formattedText,
        },
      ],
    };
  } catch (error) {
    console.error("search_transcripts: Database query failed:", error.message);
    return {
      content: [
        {
          type: "text",
          text: `Database query execution failed: ${error.message}`,
        },
      ],
      isError: true,
    };
  }
}
