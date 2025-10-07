const express = require('express');
const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');
const { run } = require('../db');

const router = express.Router();

/** POST /auth/signup  (coaches only) */
router.post('/signup', async (req, res) => {
  const { email, password, displayName } = req.body || {};
  if (!email || !password) return res.status(400).send('email and password required');

  try {
    // already registered?
    const exists = await run('SELECT id FROM users WHERE email = @email', { email });
    if (exists.recordset.length) return res.status(409).send('Email already registered');

    const hash = await bcrypt.hash(password, 12);

    // create coach user as active
    const insert = await run(`
      INSERT INTO users (email, password_hash, role_code, status_code)
      OUTPUT inserted.id, inserted.role_code
      VALUES (@email, @hash, N'coach', N'active')
    `, { email, hash });

    const user = insert.recordset[0];

    // issue JWT
    const token = jwt.sign(
      { user_id: user.id, role_code: user.role_code },
      process.env.JWT_SECRET,
      { expiresIn: '12h' }
    );

    res.json({ token });
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
      'SELECT TOP 1 id, password_hash, role_code, status_code FROM users WHERE email = @email',
      { email }
    );
    if (!q.recordset.length) return res.status(401).send('Invalid credentials');

    const u = q.recordset[0];
    if (u.status_code !== 'active') return res.status(403).send('Account not active');

    const ok = await bcrypt.compare(password, u.password_hash);
    if (!ok) return res.status(401).send('Invalid credentials');

    const token = jwt.sign(
      { user_id: u.id, role_code: u.role_code },
      process.env.JWT_SECRET,
      { expiresIn: '12h' }
    );

    res.json({ token });
  } catch (e) {
    console.error(e);
    res.status(500).send('Login failed');
}
});

module.exports = router;
