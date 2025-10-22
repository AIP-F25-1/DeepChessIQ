require('dotenv').config();
const express = require('express');
const cors = require('cors');

const authRoutes = require('./routes/auth');
const testdbRoutes = require('./routes/testdb');
const invitesRouter = require('./routes/invites');
const { verifyConnection } = require('./services/mailer');

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

/**
 * CORS
 * Accepts CLIENT_ORIGIN or APP_PUBLIC_URL (comma-separated list supported).
 */
const corsList = (process.env.APP_PUBLIC_URL || '')
  .split(',')
  .map(s => s.trim())
  .filter(Boolean);

app.use(cors({
  origin: corsList.length ? corsList : ['http://localhost:5173'],
  credentials: true
}));

app.use(express.json());

/** Health check */
app.get('/healthz', (_req, res) => res.json({ ok: true }));

/** Routes */
app.use('/auth', authRoutes);
app.use('/db', testdbRoutes);
/**
 * invitesRouter provides:
 *   POST   /coach/invites
 *   GET    /invites/:token
 *   POST   /auth/signup-from-invite
 */
app.use('/', invitesRouter);

/** SMTP self-check (non-blocking) */
verifyConnection()
  .then(() => console.log('SMTP ready'))
  .catch(err => console.error('SMTP verify failed:', err.message));

/** Start */
const PORT = Number(process.env.PORT) || 3000;
app.listen(PORT, () => console.log(`🚀 API listening on :${PORT}`));
