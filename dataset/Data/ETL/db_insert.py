import pyodbc

def insert_game(cur: pyodbc.Cursor, core_row: dict, text_row: dict) -> int | None:
    """
    Insert one game into dbo.game_core and dbo.game_text using the provided cursor.
    Returns the new game_pk, or None if duplicate (hash_loose unique).
    NOTE: Do NOT commit here; caller manages transactions.
    """
    try:
        # core
        cols = list(core_row.keys())
        sql = f"""
            INSERT INTO dbo.game_core ({", ".join(cols)})
            OUTPUT INSERTED.game_pk
            VALUES ({", ".join(["?"] * len(cols))})
        """
        cur.execute(sql, [core_row[c] for c in cols])
        game_pk = cur.fetchone()[0]

        # text
        cur.execute(
            "INSERT INTO dbo.game_text (game_pk, pgn_san, pgn_movetext_full, uci_seq) VALUES (?, ?, ?, ?)",
            (
                game_pk,
                text_row.get("pgn_san"),
                text_row.get("pgn_movetext_full"),
                text_row.get("uci_seq"),
            ),
        )
        return game_pk

    except pyodbc.IntegrityError as e:
        # If unique index on hash_loose is hit, treat as duplicate
        if "hash_loose" in str(e) or "unique" in str(e).lower():
            return None
        raise
