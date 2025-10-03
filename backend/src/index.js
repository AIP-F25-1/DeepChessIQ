const express = require('express');
const { getPool } = require('./db');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 3000;

// Simple route that uses the pool
app.get('/test', async (req, res) => {
  try {
    const pool = await getPool();
    const result = await pool.request().query('SELECT TOP 5 name FROM sys.databases');
    res.json(result.recordset);
  } catch (err) {
    console.error('DB query failed:', err);
    res.status(500).send('DB query failed');
  }
});

// Start server **after** DB is reachable
(async () => {
  try {
    await getPool(); // wait for DB
    app.listen(PORT, () => console.log(`🚀 Server running on http://localhost:${PORT}`));
  } catch (e) {
    console.error('Startup aborted: cannot reach DB.');
    process.exit(1);
  }
})();
