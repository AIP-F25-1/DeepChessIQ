const sql = require('mssql');
require('dotenv').config();

const config = {
  user: process.env.DB_USER,                 // 'Squares'
  password: process.env.DB_PASSWORD,         // 'Chess@123'
  server: process.env.DB_SERVER,             // '64squares.database.windows.net'
  database: process.env.DB_DATABASE,         // '64squares'
  port: parseInt(process.env.DB_PORT || '1433', 10),
  options: {
    encrypt: process.env.DB_ENCRYPT === 'true', // must be true for Azure SQL
    trustServerCertificate: false               // must be false for Azure SQL
  },
  pool: {
    max: 10,
    min: 0,
    idleTimeoutMillis: 30000
  },
  connectionTimeout: 30000, // 30s
  requestTimeout: 30000
};

let poolPromise;

/** Get (or create) a shared pool */
function getPool() {
  if (!poolPromise) {
    poolPromise = new sql.ConnectionPool(config)
      .connect()
      .then(pool => {
        console.log('✅ Connected to Azure SQL');
        return pool;
      })
      .catch(err => {
        console.error('❌ DB connect error:', err);
        poolPromise = null; // allow retry on next call if needed
        throw err;
      });
  }
  return poolPromise;
}

module.exports = { sql, getPool };
