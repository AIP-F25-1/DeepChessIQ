// routes/invites.js
const express = require('express');
const crypto = require('crypto');
const jwt = require('jsonwebtoken');
const bcrypt = require('bcryptjs');
const { run } = require('../db');           // your existing DB helper
const authGuard = require('../middleware/authGuard');
const { sendInviteEmail } = require('../services/mailer');

const router = express.Router();

/**
 * Coach creates an invite for a student (role 'user')
 * POST /coach/invites   { email }
 * Requires: Authorization: Bearer <coach JWT>
 * Returns: { inviteLink }
 */
router.post('/coach/invites', authGuard('coach'), async (req, res) => {
  try {
    const { email } = req.body || {};
    if (!email) return res.status(400).json({ error: 'Email required' });

    // Revoke any previous pending invite for the same email
    await run(`
      UPDATE dbo.invitations
         SET revoked_at = SYSUTCDATETIME()
       WHERE email = @email AND accepted_at IS NULL AND revoked_at IS NULL
    `, { email });

    const token = crypto.randomBytes(24).toString('base64url');
    const expiresAt = new Date(Date.now() + 7 * 24 * 60 * 60 * 1000); // 7 days

    await run(`
      INSERT INTO dbo.invitations (email, role_code, coach_id, token, expires_at)
      VALUES (@email, N'user', @coachId, @token, @expiresAt)
    `, { email, coachId: req.user.user_id, token, expiresAt });

    const base = process.env.APP_PUBLIC_URL || 'http://localhost:3000';
    const inviteLink = `${base}/invite?token=${encodeURIComponent(token)}`;

    await sendInviteEmail(email, inviteLink, req.user.name || 'Your coach');
    return res.status(201).json({ inviteLink, sent: true });
  } catch (e) {
    console.error('Create invite error:', e);
    return res.status(500).json({ error: 'Server error' });
  }
});

/**
 * Validate an invite token (for the signup page)
 * GET /invites/:token
 */
router.get('/invites/:token', async (req, res) => {
  try {
    const { token } = req.params;

    const { recordset } = await run(`
      SELECT TOP 1 email, role_code, coach_id, expires_at, accepted_at, revoked_at
      FROM dbo.invitations WHERE token = @token
    `, { token });

    const inv = recordset[0];
    if (!inv) return res.status(404).json({ error: 'Invalid link' });
    const now = new Date();
    if (inv.revoked_at || inv.accepted_at || now > inv.expires_at) {
      return res.status(410).json({ error: 'Link expired or used' });
    }

    return res.json({ email: inv.email, role: inv.role_code });
  } catch (e) {
    console.error('Validate invite error:', e);
    return res.status(500).json({ error: 'Server error' });
  }
});

/**
 * Complete signup using invite token
 * POST /auth/signup-from-invite   { token, password, name? }
 * Returns: { token: <student JWT> }
 */
router.post('/auth/signup-from-invite', async (req, res) => {
  try {
    const { token, password } = req.body || {};
    if (!token || !password) {
      return res.status(400).json({ error: 'Token and password required' });
    }

    const invRows = await run(`SELECT TOP 1 * FROM dbo.invitations WHERE token=@token`, { token });
    const inv = invRows.recordset[0];
    if (!inv) return res.status(404).json({ error: 'Invalid link' });

    const now = new Date();
    if (inv.revoked_at || inv.accepted_at || now > inv.expires_at) {
      return res.status(410).json({ error: 'Link expired or used' });
    }

    // Does user already exist?
    const existing = await run(`
      SELECT TOP 1 id, role_code FROM dbo.users WHERE email = @email
    `, { email: inv.email });

    let studentId;
    const hash = await bcrypt.hash(password, 12);

    if (existing.recordset.length) {
      const u = existing.recordset[0];
      if (u.role_code !== 'user') {
        return res.status(409).json({ error: 'Email already used with a different role' });
      }
      // update password
      await run(`UPDATE dbo.users SET password_hash=@hash WHERE id=@id`, { hash, id: u.id });
      studentId = u.id;
    } else {
      // create a fresh student (active)
      const create = await run(`
        DECLARE @id UNIQUEIDENTIFIER = NEWID();
        INSERT INTO dbo.users (id, email, password_hash, role_code, status_code)
        VALUES (@id, @email, @hash, N'user', N'active');
        SELECT @id AS id;
      `, { email: inv.email, hash });
      studentId = create.recordset[0].id;
    }

    // mark invite used
    await run(`UPDATE dbo.invitations SET accepted_at = SYSUTCDATETIME() WHERE token=@token`, { token });

    // link coach <-> student
    await run(`
      MERGE dbo.coach_students AS tgt
      USING (SELECT @coachId AS coach_id, @studentId AS student_id) AS src
      ON (tgt.coach_id = src.coach_id AND tgt.student_id = src.student_id)
      WHEN MATCHED THEN UPDATE SET status_code = N'active'
      WHEN NOT MATCHED THEN
        INSERT (coach_id, student_id, status_code)
        VALUES (src.coach_id, src.student_id, N'active');
    `, { coachId: inv.coach_id, studentId });

    // issue JWT for the student
    const studentJwt = jwt.sign(
      { user_id: studentId, role_code: 'user' },
      process.env.JWT_SECRET,
      { expiresIn: '12h' }
    );

    return res.status(201).json({ token: studentJwt });
  } catch (e) {
    console.error('Signup-from-invite error:', e);
    return res.status(500).json({ error: 'Server error' });
  }
});

module.exports = router;
