import { query } from "../database.js";

/**
 * Tool metadata and input schema definition for list_meetings.
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
 * Execution handler for list_meetings.
 * Validates inputs, queries PostgreSQL using pg connection pool, and returns results.
 *
 * @param {object} args - Tool arguments.
 * @returns {Promise<object>}
 */
export async function handler(args) {
  console.error("list_meetings tool invoked with args:", args);

  // 1. Parameter parsing & defaults
  const limit = args.limit !== undefined ? args.limit : 10;
  const offset = args.offset !== undefined ? args.offset : 0;
  const rawStatus = args.status !== undefined ? args.status : null;

  // 2. Input Validation
  if (typeof limit !== "number" || !Number.isInteger(limit) || limit < 1 || limit > 100) {
    return {
      content: [
        {
          type: "text",
          text: `Invalid parameter 'limit': must be an integer between 1 and 100. Got: ${limit}`,
        },
      ],
      isError: true,
    };
  }

  if (typeof offset !== "number" || !Number.isInteger(offset) || offset < 0) {
    return {
      content: [
        {
          type: "text",
          text: `Invalid parameter 'offset': must be a non-negative integer. Got: ${offset}`,
        },
      ],
      isError: true,
    };
  }

  const validStatuses = ["pending", "processing", "completed", "failed"];
  if (rawStatus !== null && !validStatuses.includes(rawStatus)) {
    return {
      content: [
        {
          type: "text",
          text: `Invalid parameter 'status': must be one of ${validStatuses.join(", ")}. Got: ${rawStatus}`,
        },
      ],
      isError: true,
    };
  }

  // 3. Map status value to uppercase matching database enum definition
  const status = rawStatus ? rawStatus.toUpperCase() : null;

  // 4. Database Execution using parameterized SQL with enum casting
  try {
    const sql = `
      SELECT
          id,
          title,
          meeting_date,
          duration_minutes,
          source,
          status,
          summary,
          created_at
      FROM meetings
      WHERE ($1::text IS NULL OR status = $1::meeting_status)
      ORDER BY created_at DESC
      LIMIT $2
      OFFSET $3;
    `;
    const params = [status, limit, offset];
    const res = await query(sql, params);

    // Return formatted JSON string
    return {
      content: [
        {
          type: "text",
          text: JSON.stringify({ meetings: res.rows }, null, 2),
        },
      ],
    };
  } catch (error) {
    console.error("list_meetings: Database query failed:", error.message);
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
