// src/db.js
const sql = require('mssql');
require('dotenv').config();

const config = {
  user: process.env.DB_USER,
  password: process.env.DB_PASSWORD,
  server: process.env.DB_SERVER,
  database: process.env.DB_DATABASE,
  port: parseInt(process.env.DB_PORT || '1433', 10),
  options: { encrypt: process.env.DB_ENCRYPT === 'true', trustServerCertificate: false }
};

// Call run('SELECT ... WHERE id = @id', { id: 1 })
async function run(query, params = {}) {
  const pool = await sql.connect(config);          // uses a global shared pool internally
  const req = pool.request();
  for (const [name, value] of Object.entries(params)) req.input(name, value);
  const result = await req.query(query);
  return result;
}

module.exports = { run };
