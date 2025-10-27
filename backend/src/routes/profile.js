const express = require('express');
const { run } = require('../db');
const authGuard = require('../middleware/authGuard');

const router = express.Router();

/**
 * GET /api/profile
 * Get current user's profile information
 */
router.get('/', authGuard(), async (req, res) => {
  try {
    const userId = req.user.user_id;

    const query = `
      SELECT 
        u.id,
        u.email,
        u.display_name,
        u.role_code,
        up.bio,
        up.avatar_url,
        up.country,
        up.timezone,
        up.language,
        up.join_date,
        up.last_active
      FROM users u
      LEFT JOIN user_profiles up ON u.id = up.user_id
      WHERE u.id = @userId
    `;

    const result = await run(query, { userId });

    if (!result.recordset.length) {
      return res.status(404).json({ error: 'Profile not found' });
    }

    const profile = result.recordset[0];
    res.json({
      id: profile.id,
      email: profile.email,
      username: profile.display_name || profile.email.split('@')[0],
      role: profile.role_code,
      bio: profile.bio,
      avatarUrl: profile.avatar_url,
      country: profile.country,
      timezone: profile.timezone || 'UTC',
      language: profile.language || 'en',
      joinDate: profile.join_date,
      lastActive: profile.last_active,
    });
  } catch (error) {
    console.error('Get profile error:', error);
    res.status(500).json({ error: 'Failed to fetch profile' });
  }
});

/**
 * PUT /api/profile
 * Update current user's profile information
 */
router.put('/', authGuard(), async (req, res) => {
  try {
    const userId = req.user.user_id;
    const { displayName, bio, country, timezone, language } = req.body;

    // Update users table (display_name)
    if (displayName !== undefined) {
      await run(
        'UPDATE users SET display_name = @displayName WHERE id = @userId',
        { userId, displayName }
      );
    }

    // Update user_profiles table
    const profileUpdates = [];
    const params = { userId };

    if (bio !== undefined) {
      profileUpdates.push('bio = @bio');
      params.bio = bio;
    }
    if (country !== undefined) {
      profileUpdates.push('country = @country');
      params.country = country;
    }
    if (timezone !== undefined) {
      profileUpdates.push('timezone = @timezone');
      params.timezone = timezone;
    }
    if (language !== undefined) {
      profileUpdates.push('language = @language');
      params.language = language;
    }

    if (profileUpdates.length > 0) {
      profileUpdates.push('updated_at = GETUTCDATE()');
      const updateQuery = `
        UPDATE user_profiles 
        SET ${profileUpdates.join(', ')}
        WHERE user_id = @userId
      `;
      await run(updateQuery, params);
    }

    // Fetch and return updated profile
    const result = await run(
      `
      SELECT 
        u.id,
        u.email,
        u.display_name,
        u.role_code,
        up.bio,
        up.avatar_url,
        up.country,
        up.timezone,
        up.language,
        up.join_date,
        up.last_active
      FROM users u
      LEFT JOIN user_profiles up ON u.id = up.user_id
      WHERE u.id = @userId
    `,
      { userId }
    );

    const profile = result.recordset[0];
    res.json({
      id: profile.id,
      email: profile.email,
      username: profile.display_name || profile.email.split('@')[0],
      role: profile.role_code,
      bio: profile.bio,
      avatarUrl: profile.avatar_url,
      country: profile.country,
      timezone: profile.timezone || 'UTC',
      language: profile.language || 'en',
      joinDate: profile.join_date,
      lastActive: profile.last_active,
    });
  } catch (error) {
    console.error('Update profile error:', error);
    res.status(500).json({ error: 'Failed to update profile' });
  }
});

module.exports = router;

