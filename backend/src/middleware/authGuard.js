// middleware/authGuard.js
const jwt = require('jsonwebtoken');

module.exports = function authGuard(requiredRole /* e.g., 'coach' */) {
  return (req, res, next) => {
    const hdr = req.headers.authorization || '';
    const [, token] = hdr.split(' ');
    if (!token) return res.status(401).json({ error: 'Missing token' });

    try {
      const payload = jwt.verify(token, process.env.JWT_SECRET);
      if (requiredRole && payload.role_code !== requiredRole) {
        return res.status(403).json({ error: 'Forbidden' });
      }
      req.user = payload; // { user_id, role_code, ... }
      next();
    } catch {
      return res.status(401).json({ error: 'Invalid token' });
    }
  };
};
