/* dataset/Data/SQL/2025-elo-bin-and-indexes.sql
   Adds:
     - Persisted computed column: elo_bin_100
     - Essential indexes:
         * Unique on hash_loose (dedup)
         * Nonclustered on elo_bin_100 (fast per-bin queries)
*/

SET NOCOUNT ON;

/* 1) Ensure computed column exists (persisted) */
IF COL_LENGTH('dbo.game_core', 'elo_bin_100') IS NULL
BEGIN
  PRINT 'Adding computed column dbo.game_core.elo_bin_100...';
  ALTER TABLE dbo.game_core
  ADD elo_bin_100 AS (
      (((ISNULL(white_elo, black_elo) + ISNULL(black_elo, white_elo)) / 2) / 100) * 100
  ) PERSISTED;
END
ELSE
BEGIN
  PRINT 'Computed column elo_bin_100 already exists.';
END
GO

/* 2) Ensure unique index on hash_loose for deduplication */
IF NOT EXISTS (
    SELECT 1
    FROM sys.indexes
    WHERE name = 'UX_game_core_hash_loose'
      AND object_id = OBJECT_ID('dbo.game_core')
)
BEGIN
  PRINT 'Creating unique index UX_game_core_hash_loose on dbo.game_core(hash_loose)...';
  CREATE UNIQUE INDEX UX_game_core_hash_loose ON dbo.game_core(hash_loose);
END
ELSE
BEGIN
  PRINT 'Index UX_game_core_hash_loose already exists.';
END
GO

/* 3) Ensure nonclustered index on elo_bin_100 for fast bin filters & counts */
IF NOT EXISTS (
    SELECT 1
    FROM sys.indexes
    WHERE name = 'IX_game_core_elo_bin'
      AND object_id = OBJECT_ID('dbo.game_core')
)
BEGIN
  PRINT 'Creating index IX_game_core_elo_bin on dbo.game_core(elo_bin_100)...';
  CREATE INDEX IX_game_core_elo_bin ON dbo.game_core(elo_bin_100);
END
ELSE
BEGIN
  PRINT 'Index IX_game_core_elo_bin already exists.';
END
GO
