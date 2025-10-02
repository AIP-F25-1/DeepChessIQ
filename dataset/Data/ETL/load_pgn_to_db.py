import sys, json, time
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

from DeepChessIQ.dataset.Data.ETL.db_connection import get_connection
from DeepChessIQ.dataset.Data.ETL.db_insert import insert_game
from DeepChessIQ.dataset.Data.ETL.pgn_sampler import sample_games_by_elo_bin_streaming

PGN_FILE = Path(r"C:\Users\ppava\Desktop\Projects\AIP\DeepChessIQ\Data\lichess_db_standard_rated_2025-08.pgn")
SITE = "lichess"
ELO_BINS = list(range(1500, 3100, 100))
GAMES_PER_BIN = 10000
SEED = 42

CHECKPOINT = Path("sampler_checkpoint.json")


def load_checkpoint() -> dict[int, int]:
    if CHECKPOINT.exists():
        try:
            data = json.loads(CHECKPOINT.read_text(encoding="utf-8"))
            return {int(k): int(v) for k, v in data.get("emitted_per_bin", {}).items()}
        except Exception:
            pass
    return {b: 0 for b in ELO_BINS}


def save_checkpoint(emitted_per_bin: dict[int, int], totals: dict[str, int]):
    payload = {"emitted_per_bin": {str(k): int(v) for k, v in emitted_per_bin.items()}, "totals": totals}
    CHECKPOINT.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def main():
    print(f"Streaming PGN from: {PGN_FILE}")
    t0 = time.time()

    emitted_per_bin = load_checkpoint()
    remaining_per_bin = {b: max(0, GAMES_PER_BIN - emitted_per_bin.get(b, 0)) for b in ELO_BINS}
    if all(v == 0 for v in remaining_per_bin.values()):
        print("All bins already complete per checkpoint. Nothing to do.")
        return

    inserted = 0
    duplicates = 0
    failed = 0
    processed = 0

    with get_connection() as conn:
        for core_row, text_row, b in sample_games_by_elo_bin_streaming(
            pgn_path=PGN_FILE,
            elo_bins=ELO_BINS,
            games_per_bin=GAMES_PER_BIN,
            site=SITE,
            seed=SEED,
            allowed_variants={"Standard"},
            rated_only=True,
            min_year=2019,
            min_plies=8,
            exclude_bots=True,
            max_games_per_player_per_bin=2,
            chunk_size_per_bin=400,
        ):
            if emitted_per_bin.get(b, 0) >= GAMES_PER_BIN:
                continue

            processed += 1
            try:
                game_pk = insert_game(conn, core_row, text_row)
                if game_pk:
                    inserted += 1
                    emitted_per_bin[b] = emitted_per_bin.get(b, 0) + 1
                else:
                    duplicates += 1
            except Exception as e:
                failed += 1
                if failed <= 5:
                    print(f"Insert failed (bin {b}): {e}")

            if processed % 500 == 0:
                print(f"Processed {processed} | Inserted: {inserted} | Duplicates: {duplicates} | Failed: {failed}")
                save_checkpoint(emitted_per_bin, {"inserted": inserted, "duplicates": duplicates, "failed": failed})

            if all(emitted_per_bin.get(x, 0) >= GAMES_PER_BIN for x in ELO_BINS):
                break

    save_checkpoint(emitted_per_bin, {"inserted": inserted, "duplicates": duplicates, "failed": failed})

    print("Done")
    print(f"Inserted:   {inserted}")
    print(f"Duplicates: {duplicates}")
    print(f"Failed:     {failed}")
    print(f"Time:       {time.time() - t0:.2f} seconds")


if __name__ == "__main__":
    main()
