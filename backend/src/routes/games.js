const express = require('express');
const { run } = require('../db');
const authGuard = require('../middleware/authGuard');

const router = express.Router();

/**
 * GET /api/games
 * Get user's game history with optional filtering
 */
router.get('/', authGuard(), async (req, res) => {
  try {
    const userId = req.user.user_id;
    const { result: resultFilter, limit = 50, offset = 0 } = req.query;

    let whereClause = 'WHERE user_id = @userId';
    const params = { userId, limit: parseInt(limit), offset: parseInt(offset) };

    if (resultFilter && ['win', 'loss', 'draw'].includes(resultFilter)) {
      whereClause += ' AND result = @resultFilter';
      params.resultFilter = resultFilter;
    }

    const query = `
      SELECT 
        id,
        opponent_type,
        opponent_name,
        result,
        user_color,
        total_moves,
        opening_name,
        time_control,
        user_rating,
        rating_change,
        game_duration_seconds,
        played_at
      FROM games
      ${whereClause}
      ORDER BY played_at DESC
      OFFSET @offset ROWS
      FETCH NEXT @limit ROWS ONLY
    `;

    const result = await run(query, params);

    const games = result.recordset.map(game => ({
      id: game.id.toString(),
      date: game.played_at,
      opponent: game.opponent_name,
      result: game.result,
      moves: game.total_moves,
      opening: game.opening_name || 'Unknown Opening',
      timeControl: game.time_control,
      rating: game.user_rating,
      ratingChange: game.rating_change,
      duration: game.game_duration_seconds 
        ? `${Math.floor(game.game_duration_seconds / 60)} min` 
        : null,
    }));

    res.json({ games });
  } catch (error) {
    console.error('Get games error:', error);
    res.status(500).json({ error: 'Failed to fetch games' });
  }
});

/**
 * GET /api/games/:id
 * Get specific game details including PGN
 */
router.get('/:id', authGuard(), async (req, res) => {
  try {
    const userId = req.user.user_id;
    const gameId = req.params.id;

    const query = `
      SELECT 
        id,
        opponent_type,
        opponent_name,
        result,
        user_color,
        total_moves,
        opening_name,
        time_control,
        user_rating,
        rating_change,
        pgn_data,
        fen_final,
        game_duration_seconds,
        played_at
      FROM games
      WHERE id = @gameId AND user_id = @userId
    `;

    const result = await run(query, { gameId, userId });

    if (!result.recordset.length) {
      return res.status(404).json({ error: 'Game not found' });
    }

    const game = result.recordset[0];
    res.json({
      id: game.id.toString(),
      date: game.played_at,
      opponent: game.opponent_name,
      opponentType: game.opponent_type,
      result: game.result,
      playerColor: game.user_color,
      moves: game.total_moves,
      opening: game.opening_name || 'Unknown Opening',
      timeControl: game.time_control,
      rating: game.user_rating,
      ratingChange: game.rating_change,
      pgn: game.pgn_data,
      finalFen: game.fen_final,
      duration: game.game_duration_seconds 
        ? `${Math.floor(game.game_duration_seconds / 60)} min` 
        : null,
    });
  } catch (error) {
    console.error('Get game error:', error);
    res.status(500).json({ error: 'Failed to fetch game' });
  }
});

/**
 * POST /api/games
 * Save a new game
 */
router.post('/', authGuard(), async (req, res) => {
  try {
    const userId = req.user.user_id;
    const {
      result,
      userColor = 'w',
      totalMoves,
      openingName,
      timeControl = '10+0',
      ratingChange = 0,
      pgn,
      finalFen,
      durationSeconds,
      opponentType = 'bot',
      opponentName = 'ChessIQ Bot',
    } = req.body;

    // Validation
    if (!result || !['win', 'loss', 'draw'].includes(result)) {
      return res.status(400).json({ error: 'Invalid result. Must be win, loss, or draw' });
    }
    if (!totalMoves || totalMoves < 0) {
      return res.status(400).json({ error: 'Invalid total moves' });
    }

    // Get current rating
    const statsResult = await run(
      'SELECT current_rating FROM user_statistics WHERE user_id = @userId',
      { userId }
    );
    const currentRating = statsResult.recordset.length 
      ? statsResult.recordset[0].current_rating 
      : 1200;

    // Insert game
    const insertQuery = `
      INSERT INTO games (
        user_id,
        opponent_type,
        opponent_name,
        result,
        user_color,
        total_moves,
        opening_name,
        time_control,
        user_rating,
        rating_change,
        pgn_data,
        fen_final,
        game_duration_seconds,
        played_at
      )
      OUTPUT inserted.id
      VALUES (
        @userId, @opponentType, @opponentName, @result, @userColor,
        @totalMoves, @openingName, @timeControl, @userRating, @ratingChange,
        @pgn, @finalFen, @durationSeconds, GETUTCDATE()
      )
    `;

    const insertResult = await run(insertQuery, {
      userId,
      opponentType,
      opponentName,
      result,
      userColor,
      totalMoves,
      openingName: openingName || null,
      timeControl,
      userRating: currentRating,
      ratingChange,
      pgn: pgn || null,
      finalFen: finalFen || null,
      durationSeconds: durationSeconds || null,
    });

    const gameId = insertResult.recordset[0].id;

    // Calculate new rating
    const newRating = currentRating + ratingChange;

    // Record rating change
    await run(
      `INSERT INTO chess_ratings (user_id, rating, rating_change, game_id) 
       VALUES (@userId, @newRating, @ratingChange, @gameId)`,
      { userId, newRating, ratingChange, gameId }
    );

    // Update statistics
    await updateUserStatistics(userId, result, newRating, durationSeconds);

    res.status(201).json({
      message: 'Game saved successfully',
      gameId: gameId.toString(),
      newRating,
    });
  } catch (error) {
    console.error('Save game error:', error);
    res.status(500).json({ error: 'Failed to save game' });
  }
});

/**
 * DELETE /api/games/:id
 * Delete a game
 */
router.delete('/:id', authGuard(), async (req, res) => {
  try {
    const userId = req.user.user_id;
    const gameId = req.params.id;

    // Verify game belongs to user
    const checkResult = await run(
      'SELECT id FROM games WHERE id = @gameId AND user_id = @userId',
      { gameId, userId }
    );

    if (!checkResult.recordset.length) {
      return res.status(404).json({ error: 'Game not found' });
    }

    // Delete game (cascade will delete related chess_ratings)
    await run('DELETE FROM games WHERE id = @gameId', { gameId });

    // Recalculate statistics
    await recalculateUserStatistics(userId);

    res.json({ message: 'Game deleted successfully' });
  } catch (error) {
    console.error('Delete game error:', error);
    res.status(500).json({ error: 'Failed to delete game' });
  }
});

/**
 * Helper function to update user statistics after a game
 */
async function updateUserStatistics(userId, result, newRating, durationSeconds) {
  // Get current stats
  const statsResult = await run(
    'SELECT * FROM user_statistics WHERE user_id = @userId',
    { userId }
  );

  let stats = statsResult.recordset[0] || {
    total_games: 0,
    wins: 0,
    losses: 0,
    draws: 0,
    current_streak_type: null,
    current_streak_count: 0,
    avg_game_duration_seconds: 0,
    games_this_week: 0,
  };

  // Update totals
  stats.total_games += 1;
  if (result === 'win') stats.wins += 1;
  else if (result === 'loss') stats.losses += 1;
  else if (result === 'draw') stats.draws += 1;

  // Update streak
  if (result === 'win' || result === 'loss') {
    if (stats.current_streak_type === result) {
      stats.current_streak_count += 1;
    } else {
      stats.current_streak_type = result;
      stats.current_streak_count = 1;
    }
  }

  // Update win rate
  const winRate = stats.total_games > 0 
    ? ((stats.wins / stats.total_games) * 100).toFixed(2) 
    : 0;

  // Update average game duration
  if (durationSeconds) {
    const totalDuration = (stats.avg_game_duration_seconds || 0) * (stats.total_games - 1) + durationSeconds;
    stats.avg_game_duration_seconds = Math.floor(totalDuration / stats.total_games);
  }

  // Update peak rating
  const peakRating = Math.max(stats.peak_rating || 1200, newRating);

  // Count games this week
  const weekAgo = new Date();
  weekAgo.setDate(weekAgo.getDate() - 7);
  const weekGamesResult = await run(
    'SELECT COUNT(*) as count FROM games WHERE user_id = @userId AND played_at >= @weekAgo',
    { userId, weekAgo }
  );
  const gamesThisWeek = weekGamesResult.recordset[0].count;

  // Update statistics
  await run(
    `UPDATE user_statistics SET 
      current_rating = @newRating,
      peak_rating = @peakRating,
      total_games = @totalGames,
      wins = @wins,
      losses = @losses,
      draws = @draws,
      win_rate = @winRate,
      current_streak_type = @streakType,
      current_streak_count = @streakCount,
      avg_game_duration_seconds = @avgDuration,
      games_this_week = @gamesThisWeek,
      last_game_at = GETUTCDATE(),
      updated_at = GETUTCDATE()
    WHERE user_id = @userId`,
    {
      userId,
      newRating,
      peakRating,
      totalGames: stats.total_games,
      wins: stats.wins,
      losses: stats.losses,
      draws: stats.draws,
      winRate,
      streakType: stats.current_streak_type,
      streakCount: stats.current_streak_count,
      avgDuration: stats.avg_game_duration_seconds,
      gamesThisWeek,
    }
  );
}

/**
 * Helper function to recalculate all statistics from scratch
 */
async function recalculateUserStatistics(userId) {
  const gamesResult = await run(
    `SELECT 
      result,
      game_duration_seconds,
      user_rating,
      rating_change
    FROM games
    WHERE user_id = @userId
    ORDER BY played_at ASC`,
    { userId }
  );

  const games = gamesResult.recordset;

  let wins = 0;
  let losses = 0;
  let draws = 0;
  let totalDuration = 0;
  let durationCount = 0;
  let currentRating = 1200;
  let peakRating = 1200;
  let lastResult = null;
  let streakCount = 0;

  for (const game of games) {
    if (game.result === 'win') wins++;
    else if (game.result === 'loss') losses++;
    else if (game.result === 'draw') draws++;

    if (game.game_duration_seconds) {
      totalDuration += game.game_duration_seconds;
      durationCount++;
    }

    currentRating = game.user_rating + (game.rating_change || 0);
    peakRating = Math.max(peakRating, currentRating);

    if (game.result === lastResult && (game.result === 'win' || game.result === 'loss')) {
      streakCount++;
    } else if (game.result === 'win' || game.result === 'loss') {
      lastResult = game.result;
      streakCount = 1;
    }
  }

  const totalGames = games.length;
  const winRate = totalGames > 0 ? ((wins / totalGames) * 100).toFixed(2) : 0;
  const avgDuration = durationCount > 0 ? Math.floor(totalDuration / durationCount) : 0;

  // Count games this week
  const weekAgo = new Date();
  weekAgo.setDate(weekAgo.getDate() - 7);
  const weekGamesResult = await run(
    'SELECT COUNT(*) as count FROM games WHERE user_id = @userId AND played_at >= @weekAgo',
    { userId, weekAgo }
  );
  const gamesThisWeek = weekGamesResult.recordset[0].count;

  // Update statistics
  await run(
    `UPDATE user_statistics SET 
      current_rating = @currentRating,
      peak_rating = @peakRating,
      total_games = @totalGames,
      wins = @wins,
      losses = @losses,
      draws = @draws,
      win_rate = @winRate,
      current_streak_type = @streakType,
      current_streak_count = @streakCount,
      avg_game_duration_seconds = @avgDuration,
      games_this_week = @gamesThisWeek,
      updated_at = GETUTCDATE()
    WHERE user_id = @userId`,
    {
      userId,
      currentRating,
      peakRating,
      totalGames,
      wins,
      losses,
      draws,
      winRate,
      streakType: lastResult,
      streakCount,
      avgDuration,
      gamesThisWeek,
    }
  );
}

module.exports = router;

