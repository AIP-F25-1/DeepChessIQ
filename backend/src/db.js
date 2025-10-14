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

async function run(query, params = {}) {
  const pool = await sql.connect(config);
  const req = pool.request();
  for (const [k, v] of Object.entries(params)) req.input(k, v);
  return req.query(query);
}

module.exports = { run };
