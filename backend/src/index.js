const express = require('express');
require('dotenv').config();

const app = express();
app.use(express.json());

// test route
app.get('/', (req, res) => {
  res.send('Hello, Node.js API is running 🚀');
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`Server running at http://localhost:${PORT}`));
