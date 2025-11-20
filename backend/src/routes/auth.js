const express = require('express');
const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');
const { run } = require('../db');

const router = express.Router();

const JWT_EXPIRY = '12h';
const ACTIVE_STATUS = 'active';
const JWT_SECRET = process.env.JWT_SECRET;

function ensureSecret() {
  if (!JWT_SECRET) {
    throw new Error('JWT_SECRET is not configured');
  }
  return JWT_SECRET;
}

function signToken(payload) {
  return jwt.sign(payload, ensureSecret(), { expiresIn: JWT_EXPIRY });
}

function mapUser(record) {
  return {
    id: record.id,
    email: record.email,
    role_code: record.role_code,
    display_name: record.display_name,
  };
}

/** POST /auth/signup */
router.post('/signup', async (req, res) => {
  const { email, password, role_code = 'user', displayName } = req.body || {};
  if (!email || !password) return res.status(400).send('email and password required');
  try {
    const exists = await run('SELECT id FROM users WHERE email = @email', { email });
    if (exists.recordset.length) return res.status(409).send('Email already registered');

    const hash = await bcrypt.hash(password, 12);
    const insert = await run(
      `
      INSERT INTO users (email, password_hash, role_code, status_code, display_name)
      OUTPUT inserted.id, inserted.email, inserted.role_code, inserted.display_name
      VALUES (@email, @hash, @role, N'${ACTIVE_STATUS}', @displayName)
    `,
      { email, hash, role: role_code, displayName: displayName ?? null },
    );

    const user = mapUser(insert.recordset[0]);
    const token = signToken({ user_id: user.id, role_code: user.role_code });

    res.json({ token, user });
  } catch (e) {
    console.error(e);
    res.status(500).send('Signup failed');
  }
});

/** POST /auth/login */
router.post('/login', async (req, res) => {
  const { email, password } = req.body || {};
  if (!email || !password) return res.status(400).send('email and password required');

  try {
    const q = await run(
      'SELECT TOP 1 id, email, password_hash, role_code, status_code, display_name FROM users WHERE email = @email',
      { email },
    );
    if (!q.recordset.length) return res.status(401).send('Invalid credentials');

    const u = q.recordset[0];
    if (u.status_code !== ACTIVE_STATUS) return res.status(403).send('Account not active');

    const ok = await bcrypt.compare(password, u.password_hash);
    if (!ok) return res.status(401).send('Invalid credentials');

    const user = mapUser(u);
    const token = signToken({ user_id: user.id, role_code: user.role_code });

    res.json({ token, user });
  } catch (e) {
    console.error(e);
    res.status(500).send('Login failed');
  }
});

module.exports = router;
