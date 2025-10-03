// src/index.js
const express = require('express');
const { run } = require('./db');

const app = express();
const PORT = process.env.PORT || 3000;

app.get('/test', async (_req, res) => {
  try {
    const { recordset } = await run('SELECT TOP (5) name FROM sys.databases');
    res.json(recordset);
  } catch (e) {
    console.error(e);
    res.status(500).send('DB query failed');
  }
});

// Example with parameters
app.get('/users/:id', async (req, res) => {
  try {
    const { recordset } = await run(
      'SELECT * FROM Users WHERE Id = @id',
      { id: req.params.id }
    );
    res.json(recordset);
  } catch (e) {
    console.error(e);
    res.status(500).send('DB query failed');
  }
});

app.listen(PORT, () => console.log(`🚀 http://localhost:${PORT}`));
