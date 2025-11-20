const express = require('express');
const { run } = require('../db');

const router = express.Router();

router.get('/test', async (_req, res) => {
  try {
    const { recordset } = await run('SELECT TOP (5) name FROM sys.databases');
    res.json(recordset);
  } catch (e) {
    console.error(e);
    res.status(500).send('DB query failed');
  }
});

router.get('/users/:id', async (req, res) => {
  try {
    const { recordset } = await run('SELECT * FROM users WHERE id = @id', { id: req.params.id });
    res.json(recordset);
  } catch (e) {
    console.error(e);
    res.status(500).send('DB query failed');
  }
});

module.exports = router;
