-- =============================================
-- DeepChessIQ Core Tables Migration
-- This creates all necessary tables for the application
-- =============================================

-- Drop tables if they exist (in reverse dependency order)
IF OBJECT_ID('user_statistics', 'U') IS NOT NULL DROP TABLE user_statistics;
IF OBJECT_ID('game_settings', 'U') IS NOT NULL DROP TABLE game_settings;
IF OBJECT_ID('games', 'U') IS NOT NULL DROP TABLE games;
IF OBJECT_ID('chess_ratings', 'U') IS NOT NULL DROP TABLE chess_ratings;
IF OBJECT_ID('user_profiles', 'U') IS NOT NULL DROP TABLE user_profiles;
IF OBJECT_ID('coach_students', 'U') IS NOT NULL DROP TABLE coach_students;
IF OBJECT_ID('invitations', 'U') IS NOT NULL DROP TABLE invitations;

-- =============================================
-- Table: user_profiles
-- Extended profile information for users
-- =============================================
CREATE TABLE user_profiles (
    user_id UNIQUEIDENTIFIER PRIMARY KEY,
    bio NVARCHAR(500) NULL,
    avatar_url NVARCHAR(255) NULL,
    country NVARCHAR(50) NULL,
    timezone NVARCHAR(50) DEFAULT 'UTC',
    language NVARCHAR(10) DEFAULT 'en',
    join_date DATETIME2 DEFAULT GETUTCDATE(),
    last_active DATETIME2 DEFAULT GETUTCDATE(),
    created_at DATETIME2 DEFAULT GETUTCDATE(),
    updated_at DATETIME2 DEFAULT GETUTCDATE(),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- =============================================
-- Table: chess_ratings
-- Track rating history over time
-- =============================================
CREATE TABLE chess_ratings (
    id INT IDENTITY(1,1) PRIMARY KEY,
    user_id UNIQUEIDENTIFIER NOT NULL,
    rating INT NOT NULL DEFAULT 1200,
    rating_change INT NOT NULL DEFAULT 0,
    game_id INT NULL,
    recorded_at DATETIME2 DEFAULT GETUTCDATE(),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX idx_chess_ratings_user_date ON chess_ratings(user_id, recorded_at DESC);

-- =============================================
-- Table: games
-- Store chess game records
-- =============================================
CREATE TABLE games (
    id INT IDENTITY(1,1) PRIMARY KEY,
    user_id UNIQUEIDENTIFIER NOT NULL,
    opponent_type NVARCHAR(20) DEFAULT 'bot', -- 'bot', 'human', 'analysis'
    opponent_name NVARCHAR(100) DEFAULT 'ChessIQ Bot',
    result NVARCHAR(10) NOT NULL, -- 'win', 'loss', 'draw'
    user_color NVARCHAR(5) DEFAULT 'w', -- 'w' or 'b'
    total_moves INT NOT NULL DEFAULT 0,
    opening_name NVARCHAR(100) NULL,
    time_control NVARCHAR(20) DEFAULT '10+0',
    user_rating INT NOT NULL DEFAULT 1200,
    rating_change INT NOT NULL DEFAULT 0,
    pgn_data NVARCHAR(MAX) NULL,
    fen_final NVARCHAR(255) NULL,
    game_duration_seconds INT NULL,
    played_at DATETIME2 DEFAULT GETUTCDATE(),
    created_at DATETIME2 DEFAULT GETUTCDATE(),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX idx_games_user_played ON games(user_id, played_at DESC);
CREATE INDEX idx_games_result ON games(user_id, result);

-- =============================================
-- Table: game_settings
-- User game preferences
-- =============================================
CREATE TABLE game_settings (
    user_id UNIQUEIDENTIFIER PRIMARY KEY,
    show_legal_moves BIT DEFAULT 1,
    highlight_last_move BIT DEFAULT 1,
    board_theme NVARCHAR(50) DEFAULT 'classic',
    piece_set NVARCHAR(50) DEFAULT 'cburnett',
    auto_queen BIT DEFAULT 1,
    sound_enabled BIT DEFAULT 1,
    created_at DATETIME2 DEFAULT GETUTCDATE(),
    updated_at DATETIME2 DEFAULT GETUTCDATE(),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- =============================================
-- Table: user_statistics
-- Computed statistics for users
-- =============================================
CREATE TABLE user_statistics (
    user_id UNIQUEIDENTIFIER PRIMARY KEY,
    current_rating INT NOT NULL DEFAULT 1200,
    peak_rating INT NOT NULL DEFAULT 1200,
    total_games INT NOT NULL DEFAULT 0,
    wins INT NOT NULL DEFAULT 0,
    losses INT NOT NULL DEFAULT 0,
    draws INT NOT NULL DEFAULT 0,
    win_rate DECIMAL(5,2) DEFAULT 0.00,
    current_streak_type NVARCHAR(10) NULL, -- 'win', 'loss', null
    current_streak_count INT DEFAULT 0,
    avg_game_duration_seconds INT NULL,
    games_this_week INT DEFAULT 0,
    last_game_at DATETIME2 NULL,
    updated_at DATETIME2 DEFAULT GETUTCDATE(),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- =============================================
-- Table: invitations
-- Coach invitation system
-- =============================================
CREATE TABLE invitations (
    id INT IDENTITY(1,1) PRIMARY KEY,
    coach_id UNIQUEIDENTIFIER NOT NULL,
    token NVARCHAR(255) UNIQUE NOT NULL,
    email NVARCHAR(255) NOT NULL,
    status NVARCHAR(20) DEFAULT 'pending', -- 'pending', 'accepted', 'expired'
    expires_at DATETIME2 NOT NULL,
    created_at DATETIME2 DEFAULT GETUTCDATE(),
    accepted_at DATETIME2 NULL,
    FOREIGN KEY (coach_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX idx_invitations_token ON invitations(token);
CREATE INDEX idx_invitations_email ON invitations(email);

-- =============================================
-- Table: coach_students
-- Relationship between coaches and students
-- =============================================
CREATE TABLE coach_students (
    id INT IDENTITY(1,1) PRIMARY KEY,
    coach_id UNIQUEIDENTIFIER NOT NULL,
    student_id UNIQUEIDENTIFIER NOT NULL,
    status NVARCHAR(20) DEFAULT 'active', -- 'active', 'inactive'
    notes NVARCHAR(MAX) NULL,
    linked_at DATETIME2 DEFAULT GETUTCDATE(),
    updated_at DATETIME2 DEFAULT GETUTCDATE(),
    FOREIGN KEY (coach_id) REFERENCES users(id),
    FOREIGN KEY (student_id) REFERENCES users(id),
    UNIQUE (coach_id, student_id)
);

CREATE INDEX idx_coach_students_coach ON coach_students(coach_id, status);
CREATE INDEX idx_coach_students_student ON coach_students(student_id);

-- =============================================
-- Create default entries for existing users
-- =============================================

-- Create user_profiles for all existing users
INSERT INTO user_profiles (user_id, join_date, last_active)
SELECT id, GETUTCDATE(), GETUTCDATE()
FROM users
WHERE id NOT IN (SELECT user_id FROM user_profiles);

-- Create game_settings for all existing users
INSERT INTO game_settings (user_id)
SELECT id
FROM users
WHERE id NOT IN (SELECT user_id FROM game_settings);

-- Create user_statistics for all existing users
INSERT INTO user_statistics (user_id)
SELECT id
FROM users
WHERE id NOT IN (SELECT user_id FROM user_statistics);

-- =============================================
-- Success message
-- =============================================
PRINT 'Migration 002_core_tables.sql completed successfully!';
PRINT 'Tables created: user_profiles, chess_ratings, games, game_settings, user_statistics, invitations, coach_students';

