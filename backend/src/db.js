const sql = require('mssql');
require('dotenv').config();

const parsedPort = Number.parseInt(process.env.DB_PORT ?? '', 10);
const config = {
  user: process.env.DB_USER,
  password: process.env.DB_PASSWORD,
  server: process.env.DB_SERVER,
  database: process.env.DB_DATABASE,
  port: Number.isNaN(parsedPort) ? 1433 : parsedPort,
  options: { encrypt: process.env.DB_ENCRYPT === 'true', trustServerCertificate: false }
};

async function run(query, params = {}) {
  const pool = await sql.connect(config);
  const req = pool.request();
  for (const [k, v] of Object.entries(params)) req.input(k, v);
  return req.query(query);
}

module.exports = { run };
