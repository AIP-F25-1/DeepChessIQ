// services/mailer.js
const nodemailer = require('nodemailer');

let cachedTransport;

/**
 * Create (or reuse) a Nodemailer transport from env.
 * Works with any SMTP (SendGrid, Mailgun, SES SMTP endpoint, etc.)
 */
function getTransport() {
  if (cachedTransport) return cachedTransport;

  const host = process.env.SMTP_HOST;
  const port = Number(process.env.SMTP_PORT || 587);
  const user = process.env.SMTP_USER;
  const pass = process.env.SMTP_PASS;

  if (!host || !user || !pass) {
    throw new Error('SMTP env vars missing. Set SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS.');
  }

  cachedTransport = nodemailer.createTransport({
    host,
    port,
    secure: port === 465, // true for 465, false for 587/25
    auth: { user, pass },
  });

  return cachedTransport;
}

/**
 * Optional check you can run on startup to confirm SMTP works.
 */
async function verifyConnection() {
  const transporter = getTransport();
  await transporter.verify();
  return true;
}

/**
 * Send the student invite email with the magic link.
 * @param {string} to        student email
 * @param {string} inviteLink  full URL like https://app/invite?token=...
 * @param {string} coachName optional coach display name
 */
async function sendInviteEmail(to, inviteLink, coachName = 'Your coach') {
  const transporter = getTransport();

  const from = process.env.MAIL_FROM || 'DeepChessIQ <no-reply@deepchessiq.app>';
  const subject = 'You’ve been invited to DeepChessIQ';

  const html = `
    <div style="font-family:Arial, Helvetica, sans-serif; line-height:1.6;">
      <h2>Join DeepChessIQ</h2>
      <p>${escapeHtml(coachName)} invited you to join as a student.</p>
      <p>
        <a href="${inviteLink}" 
           style="display:inline-block;padding:10px 16px;text-decoration:none;border-radius:6px;
                  background:#1f6feb;color:#fff;font-weight:600;">
          Accept invite & set your password
        </a>
      </p>
      <p>If the button doesn't work, paste this link in your browser:</p>
      <p style="word-break:break-all;"><a href="${inviteLink}">${inviteLink}</a></p>
      <hr/>
      <p style="color:#6b7280;font-size:12px;">
        This link expires in 7 days. If you weren’t expecting this, you can ignore the email.
      </p>
    </div>
  `;

  const text = `${coachName} invited you to DeepChessIQ.
Open this link to accept and set your password:
${inviteLink}

This link expires in 7 days. If you weren’t expecting this, ignore this email.
`;

  const info = await transporter.sendMail({ from, to, subject, html, text });
  return info; // contains messageId, etc.
}

/** tiny helper to avoid HTML injection in the coach name */
function escapeHtml(s) {
  return String(s)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
}

module.exports = {
  getTransport,
  verifyConnection,
  sendInviteEmail,
};
