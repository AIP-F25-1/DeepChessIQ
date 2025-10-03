-- Tables (create only if missing)
IF OBJECT_ID('dbo.game_core','U') IS NULL
BEGIN
  CREATE TABLE dbo.game_core (
    game_pk           BIGINT IDENTITY(1,1) PRIMARY KEY,
    site              NVARCHAR(16) NOT NULL,                -- 'lichess' / 'chesscom'
    site_game_id      NVARCHAR(32) NULL,
    site_url          NVARCHAR(256) NULL,

    started_at_utc    DATETIME2 NULL,
    date_utc          DATE NULL,

    white_name        NVARCHAR(64) NULL,
    black_name        NVARCHAR(64) NULL,
    white_elo         INT NULL,
    black_elo         INT NULL,
    white_rating_diff INT NULL,
    black_rating_diff INT NULL,

    result            NVARCHAR(7) NULL,                     -- '1-0','0-1','1/2-1/2','*'
    timecontrol       NVARCHAR(32) NULL,
    eco               NVARCHAR(3) NULL,
    opening           NVARCHAR(512) NULL,
    termination       NVARCHAR(40) NULL,
    variant           NVARCHAR(40) NULL,
    round             NVARCHAR(16) NULL,
    ply_count         INT NULL,
    start_fen         NVARCHAR(200) NULL,

    -- fingerprints
    hash_loose        CHAR(32) NOT NULL,
    hash_strict       CHAR(32) NOT NULL,
    meta_key_hash     CHAR(24) NULL,

    -- helpers
    elo_avg AS (([white_elo] + [black_elo]) / 2) PERSISTED,
    elo_bin_100 AS ((([white_elo] + [black_elo]) / 2) / 100 * 100) PERSISTED
  );
END
GO

IF OBJECT_ID('dbo.game_text','U') IS NULL
BEGIN
  CREATE TABLE dbo.game_text (
    game_pk           BIGINT PRIMARY KEY
      FOREIGN KEY REFERENCES dbo.game_core(game_pk) ON DELETE CASCADE,
    uci_seq           NVARCHAR(MAX) NULL,
    pgn_san           NVARCHAR(MAX) NULL,
    pgn_movetext_full NVARCHAR(MAX) NULL
  );
END
GO

-- View to join both
CREATE OR ALTER VIEW dbo.v_game_full AS
SELECT c.*, t.uci_seq, t.pgn_san, t.pgn_movetext_full
FROM dbo.game_core c
LEFT JOIN dbo.game_text t ON t.game_pk = c.game_pk;
GO

-- Unique index to AVOID DUPLICATES by hash (duplicates become no-ops)
IF EXISTS (SELECT 1 FROM sys.indexes WHERE name='ux_game_hash_loose' AND object_id=OBJECT_ID('dbo.game_core'))
  DROP INDEX ux_game_hash_loose ON dbo.game_core;
GO
CREATE UNIQUE INDEX ux_game_hash_loose ON dbo.game_core(hash_loose)
WITH (IGNORE_DUP_KEY = ON);
GO
