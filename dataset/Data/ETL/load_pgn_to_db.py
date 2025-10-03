import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[2]))  # adds your AIP project root to sys.path


import time
from DeepChessIQ.Data.ETL.db_connection import get_connection
from DeepChessIQ.Data.ETL.db_insert import insert_game
from DeepChessIQ.Data.ETL.pgn_sampler import sample_games_by_elo_bin


# --- Config ---
PGN_FILE = Path(r"C:\Users\ppava\Desktop\Projects\AIP\DeepChessIQ\Data\lichess_db_standard_rated_2025-08.pgn")  # update if needed
SITE = "lichess"
ELO_BINS = list(range(1500, 3100, 100))  # 1500 to 3000
GAMES_PER_BIN = 10000
SEED = 42

def main():
    print(f"📂 Reading PGN from: {PGN_FILE}")
    t0 = time.time()

    games = sample_games_by_elo_bin(
        pgn_path=PGN_FILE,
        elo_bins=ELO_BINS,
        games_per_bin=GAMES_PER_BIN,
        site=SITE,
        seed=SEED
    )

    print(f"🎯 Sampled {len(games)} games from PGN")

    inserted = 0
    duplicates = 0
    failed = 0

    with get_connection() as conn:
        for i, (core_row, text_row) in enumerate(games, 1):
            try:
                game_pk = insert_game(conn, core_row, text_row)
                if game_pk:
                    inserted += 1
                else:
                    duplicates += 1
            except Exception as e:
                failed += 1
                print(f"❌ Failed on game #{i}: {e}")

            if i % 500 == 0:
                print(f"➡️  Processed {i} games... (inserted: {inserted}, dupes: {duplicates})")

    print("✅ DONE")
    print(f"✅ Inserted:   {inserted}")
    print(f"🔁 Duplicates: {duplicates}")
    print(f"❌ Failed:     {failed}")
    print(f"⏱️  Time:       {time.time() - t0:.2f} seconds")

if __name__ == "__main__":
    main()
