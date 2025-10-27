const express = require('express');
const { run } = require('../db');
const authGuard = require('../middleware/authGuard');

const router = express.Router();

/**
 * GET /api/statistics
 * Get user's chess statistics
 */
router.get('/', authGuard(), async (req, res) => {
  try {
    const userId = req.user.user_id;

    const query = `
      SELECT 
        current_rating,
        peak_rating,
        total_games,
        wins,
        losses,
        draws,
        win_rate,
        current_streak_type,
        current_streak_count,
        avg_game_duration_seconds,
        games_this_week,
        last_game_at
      FROM user_statistics
      WHERE user_id = @userId
    `;

    const result = await run(query, { userId });

    if (!result.recordset.length) {
      // Create default statistics if not exists
      await run(
        'INSERT INTO user_statistics (user_id) VALUES (@userId)',
        { userId }
      );

      return res.json({
        currentRating: 1200,
        peakRating: 1200,
        totalGamesPlayed: 0,
        wins: 0,
        losses: 0,
        draws: 0,
        winRatePercentage: 0,
        currentStreak: { type: 'none', count: 0 },
        averageGameDuration: '0 min',
        gamesThisWeek: 0,
        lastGameDate: null,
      });
    }

    const stats = result.recordset[0];

    // Format average game duration
    const avgMinutes = stats.avg_game_duration_seconds 
      ? Math.floor(stats.avg_game_duration_seconds / 60) 
      : 0;
    const avgSeconds = stats.avg_game_duration_seconds 
      ? stats.avg_game_duration_seconds % 60 
      : 0;
    const avgDuration = avgMinutes > 0 
      ? `${avgMinutes} min${avgSeconds > 0 ? ` ${avgSeconds} sec` : ''}`
      : '0 min';

    res.json({
      currentRating: stats.current_rating,
      peakRating: stats.peak_rating,
      totalGamesPlayed: stats.total_games,
      wins: stats.wins,
      losses: stats.losses,
      draws: stats.draws,
      winRatePercentage: parseFloat(stats.win_rate) || 0,
      currentStreak: {
        type: stats.current_streak_type || 'none',
        count: stats.current_streak_count || 0,
      },
      averageGameDuration: avgDuration,
      gamesThisWeek: stats.games_this_week,
      lastGameDate: stats.last_game_at,
    });
  } catch (error) {
    console.error('Get statistics error:', error);
    res.status(500).json({ error: 'Failed to fetch statistics' });
  }
});

/**
 * GET /api/statistics/ratings/history
 * Get rating history for charts
 */
router.get('/ratings/history', authGuard(), async (req, res) => {
  try {
    const userId = req.user.user_id;
    const { limit = 30 } = req.query;

    const query = `
      SELECT TOP (@limit)
        rating,
        rating_change,
        recorded_at
      FROM chess_ratings
      WHERE user_id = @userId
      ORDER BY recorded_at DESC
    `;

    const result = await run(query, { userId, limit: parseInt(limit) });

    const history = result.recordset.map(record => ({
      rating: record.rating,
      ratingChange: record.rating_change,
      date: record.recorded_at,
    })).reverse(); // Reverse to get chronological order

    res.json({ history });
  } catch (error) {
    console.error('Get rating history error:', error);
    res.status(500).json({ error: 'Failed to fetch rating history' });
  }
});

module.exports = router;

