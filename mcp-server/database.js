import { readFileSync, existsSync } from "fs";
import path from "path";
import { fileURLToPath } from "url";
import dotenv from "dotenv";
import pg from "pg";

const { Pool } = pg;

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Load environment variables from the parent folder's .env file.
// DATABASE_URL is the single source of truth.
// Inside Docker Compose, DATABASE_URL should use the hostname "db".
// When running outside Docker, DATABASE_URL should typically use "localhost"
// (or whatever hostname is explicitly configured by the user).
// The application never rewrites or modifies DATABASE_URL.
//
// IMPORTANT: We use dotenv.parse() instead of dotenv.config() because
// dotenv v17.x writes a status line to stdout, which corrupts the
// MCP stdio transport (stdout is reserved exclusively for JSON-RPC messages).
const envPath = path.resolve(__dirname, "../.env");
if (existsSync(envPath)) {
  const envContent = readFileSync(envPath, "utf-8");
  const parsed = dotenv.parse(envContent);
  for (const [key, value] of Object.entries(parsed)) {
    if (!(key in process.env)) {
      process.env[key] = value;
    }
  }
}

let connectionString = process.env.DATABASE_URL;

if (!connectionString) {
  console.error("database.js: DATABASE_URL environment variable is missing.");
}

let pool = null;

if (connectionString) {
  try {
    pool = new Pool({
      connectionString,
      // Fail fast on connection handshake timeouts (5 seconds)
      connectionTimeoutMillis: 5000,
      // Prevent long-running queries from hanging the server (10 seconds)
      statement_timeout: 10000,
    });

    pool.on("error", (err) => {
      console.error("database.js: Unexpected error on idle Postgres client:", err.message);
    });
  } catch (error) {
    console.error("database.js: Failed to initialize Postgres connection pool:", error.message);
  }
}

/**
 * Obtains a client from the connection pool.
 * Gracefully handles connection failures and returns meaningful errors.
 *
 * @returns {Promise<import('pg').PoolClient>}
 */
export async function getClient() {
  if (!pool) {
    throw new Error(
      "PostgreSQL pool is not initialized. Ensure DATABASE_URL is set and valid."
    );
  }
  try {
    const client = await pool.connect();
    return client;
  } catch (error) {
    console.error("database.js: Pool client connection attempt failed:", error.message);
    throw new Error(`Database connection failed: ${error.message}`);
  }
}

/**
 * Executes a parameterized SQL query on the database.
 * Gracefully handles query execution failures.
 *
 * @param {string} text - SQL statement to execute.
 * @param {any[]} [params] - Parameterized query arguments.
 * @returns {Promise<import('pg').QueryResult>}
 */
export async function query(text, params) {
  if (!pool) {
    throw new Error(
      "PostgreSQL pool is not initialized. Ensure DATABASE_URL is set and valid."
    );
  }
  try {
    return await pool.query(text, params);
  } catch (error) {
    console.error("database.js: Query execution failed:", error.message);
    throw new Error(`Database query failed: ${error.message}`);
  }
}

/**
 * Gracefully shuts down the database connection pool.
 *
 * @returns {Promise<void>}
 */
export async function closePool() {
  if (pool) {
    console.error("database.js: Shutting down PostgreSQL connection pool...");
    await pool.end();
    console.error("database.js: PostgreSQL connection pool closed successfully.");
  }
}

export { pool };
