const express = require('express');
const bcrypt = require('bcryptjs');
const { run } = require('../db');
const authGuard = require('../middleware/authGuard');

const router = express.Router();

/**
 * GET /api/settings
 * Get user's settings (general + game settings)
 */
router.get('/', authGuard(), async (req, res) => {
  try {
    const userId = req.user.user_id;

    const query = `
      SELECT 
        u.display_name,
        u.email,
        up.timezone,
        up.language,
        gs.show_legal_moves,
        gs.highlight_last_move,
        gs.board_theme,
        gs.piece_set,
        gs.auto_queen,
        gs.sound_enabled
      FROM users u
      LEFT JOIN user_profiles up ON u.id = up.user_id
      LEFT JOIN game_settings gs ON u.id = gs.user_id
      WHERE u.id = @userId
    `;

    const result = await run(query, { userId });

    if (!result.recordset.length) {
      return res.status(404).json({ error: 'Settings not found' });
    }

    const settings = result.recordset[0];
    res.json({
      general: {
        displayName: settings.display_name,
        email: settings.email,
        language: settings.language || 'en',
        timezone: settings.timezone || 'UTC',
      },
      game: {
        showLegalMoves: settings.show_legal_moves !== false,
        highlightLastMove: settings.highlight_last_move !== false,
        boardTheme: settings.board_theme || 'classic',
        pieceSet: settings.piece_set || 'cburnett',
        autoQueen: settings.auto_queen !== false,
        soundEnabled: settings.sound_enabled !== false,
      },
    });
  } catch (error) {
    console.error('Get settings error:', error);
    res.status(500).json({ error: 'Failed to fetch settings' });
  }
});

/**
 * PUT /api/settings
 * Update user's settings
 */
router.put('/', authGuard(), async (req, res) => {
  try {
    const userId = req.user.user_id;
    const { general, game } = req.body;

    // Update general settings
    if (general) {
      const generalUpdates = [];
      const generalParams = { userId };

      if (general.displayName !== undefined) {
        await run(
          'UPDATE users SET display_name = @displayName WHERE id = @userId',
          { userId, displayName: general.displayName }
        );
      }

      if (general.language !== undefined) {
        generalUpdates.push('language = @language');
        generalParams.language = general.language;
      }
      if (general.timezone !== undefined) {
        generalUpdates.push('timezone = @timezone');
        generalParams.timezone = general.timezone;
      }

      if (generalUpdates.length > 0) {
        generalUpdates.push('updated_at = GETUTCDATE()');
        await run(
          `UPDATE user_profiles SET ${generalUpdates.join(', ')} WHERE user_id = @userId`,
          generalParams
        );
      }
    }

    // Update game settings
    if (game) {
      const gameUpdates = [];
      const gameParams = { userId };

      if (game.showLegalMoves !== undefined) {
        gameUpdates.push('show_legal_moves = @showLegalMoves');
        gameParams.showLegalMoves = game.showLegalMoves ? 1 : 0;
      }
      if (game.highlightLastMove !== undefined) {
        gameUpdates.push('highlight_last_move = @highlightLastMove');
        gameParams.highlightLastMove = game.highlightLastMove ? 1 : 0;
      }
      if (game.boardTheme !== undefined) {
        gameUpdates.push('board_theme = @boardTheme');
        gameParams.boardTheme = game.boardTheme;
      }
      if (game.pieceSet !== undefined) {
        gameUpdates.push('piece_set = @pieceSet');
        gameParams.pieceSet = game.pieceSet;
      }
      if (game.autoQueen !== undefined) {
        gameUpdates.push('auto_queen = @autoQueen');
        gameParams.autoQueen = game.autoQueen ? 1 : 0;
      }
      if (game.soundEnabled !== undefined) {
        gameUpdates.push('sound_enabled = @soundEnabled');
        gameParams.soundEnabled = game.soundEnabled ? 1 : 0;
      }

      if (gameUpdates.length > 0) {
        gameUpdates.push('updated_at = GETUTCDATE()');
        await run(
          `UPDATE game_settings SET ${gameUpdates.join(', ')} WHERE user_id = @userId`,
          gameParams
        );
      }
    }

    // Return updated settings
    const result = await run(
      `
      SELECT 
        u.display_name,
        u.email,
        up.timezone,
        up.language,
        gs.show_legal_moves,
        gs.highlight_last_move,
        gs.board_theme,
        gs.piece_set,
        gs.auto_queen,
        gs.sound_enabled
      FROM users u
      LEFT JOIN user_profiles up ON u.id = up.user_id
      LEFT JOIN game_settings gs ON u.id = gs.user_id
      WHERE u.id = @userId
    `,
      { userId }
    );

    const settings = result.recordset[0];
    res.json({
      general: {
        displayName: settings.display_name,
        email: settings.email,
        language: settings.language || 'en',
        timezone: settings.timezone || 'UTC',
      },
      game: {
        showLegalMoves: settings.show_legal_moves !== false,
        highlightLastMove: settings.highlight_last_move !== false,
        boardTheme: settings.board_theme || 'classic',
        pieceSet: settings.piece_set || 'cburnett',
        autoQueen: settings.auto_queen !== false,
        soundEnabled: settings.sound_enabled !== false,
      },
    });
  } catch (error) {
    console.error('Update settings error:', error);
    res.status(500).json({ error: 'Failed to update settings' });
  }
});

/**
 * POST /api/settings/change-password
 * Change user's password
 */
router.post('/change-password', authGuard(), async (req, res) => {
  try {
    const userId = req.user.user_id;
    const { currentPassword, newPassword } = req.body;

    if (!currentPassword || !newPassword) {
      return res.status(400).json({ error: 'Both current and new passwords are required' });
    }

    if (newPassword.length < 6) {
      return res.status(400).json({ error: 'New password must be at least 6 characters' });
    }

    // Verify current password
    const user = await run(
      'SELECT password_hash FROM users WHERE id = @userId',
      { userId }
    );

    if (!user.recordset.length) {
      return res.status(404).json({ error: 'User not found' });
    }

    const isValid = await bcrypt.compare(currentPassword, user.recordset[0].password_hash);
    if (!isValid) {
      return res.status(401).json({ error: 'Current password is incorrect' });
    }

    // Hash and update new password
    const newHash = await bcrypt.hash(newPassword, 12);
    await run(
      'UPDATE users SET password_hash = @newHash WHERE id = @userId',
      { userId, newHash }
    );

    res.json({ message: 'Password changed successfully' });
  } catch (error) {
    console.error('Change password error:', error);
    res.status(500).json({ error: 'Failed to change password' });
  }
});

module.exports = router;

