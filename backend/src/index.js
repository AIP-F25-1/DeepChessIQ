require('dotenv').config();
const express = require('express');
const cors = require('cors');
const authRoutes = require('./routes/auth');
const testRoutes = require('./routes/testdb');

const app = express();
app.use(express.json());

app.use('/auth', authRoutes);
app.use('/db', testdbRoutes);
const invitesRouter = require('./routes/invites');
app.use('/', invitesRouter); // provides /coach/invites, /invites/:token, /auth/signup-from-invite
;

const { verifyConnection } = require('./services/mailer');
verifyConnection().then(() => {
  console.log('SMTP ready');
}).catch(err => {
  console.error('SMTP verify failed:', err.message);
});

const PORT = process.env.PORT || 3000;
const allowedOrigins = process.env.CLIENT_ORIGIN
  ? process.env.CLIENT_ORIGIN.split(',').map((origin) => origin.trim())
  : ['http://localhost:5173'];

app.use(cors({ origin: allowedOrigins, credentials: true }));
app.use(express.json());

app.use('/auth', authRoutes);
app.use('/', testRoutes);

app.listen(PORT, () => console.log(`🚀 http://localhost:${PORT}`));
