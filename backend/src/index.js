require('dotenv').config();
const express = require('express');
const cors = require('cors');
const authRoutes = require('./routes/auth');
const testRoutes = require('./routes/testdb');

const app = express();

// CORS middleware - MUST be first!
app.use((req, res, next) => {
  res.header('Access-Control-Allow-Origin', '*');
  res.header('Access-Control-Allow-Methods', 'GET,POST,PUT,PATCH,DELETE,OPTIONS');
  res.header('Access-Control-Allow-Headers', 'Content-Type, Authorization');
  if (req.method === 'OPTIONS') {
    return res.sendStatus(204);
  }
  next();
});

app.use(express.json());
const invitesRouter = require('./routes/invites');

const { verifyConnection } = require('./services/mailer');
verifyConnection().then(() => {
  console.log('SMTP ready');
}).catch(err => {
  console.error('SMTP verify failed:', err.message);
});

const PORT = process.env.PORT || 3000;

// Routes (after CORS)
app.use('/auth', authRoutes);
app.use('/db', testRoutes);
app.use('/', invitesRouter); // provides /coach/invites, /invites/:token, /auth/signup-from-invite

app.listen(PORT, () => console.log(`🚀 http://localhost:${PORT}`));
