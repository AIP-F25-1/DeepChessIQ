import pyodbc
from .db_connection import get_connection

def insert_game(conn: pyodbc.Connection, core_row: dict, text_row: dict) -> int | None:
    """
    Inserts one game into game_core and game_text.
    Returns the inserted game_pk or None if duplicate.
    """
    with conn.cursor() as cur:
        try:
            # Insert into game_core
            core_columns = ", ".join(core_row.keys())
            core_placeholders = ", ".join(["?" for _ in core_row])
            core_values = list(core_row.values())

            insert_core_sql = f"""
                INSERT INTO dbo.game_core ({core_columns})
                OUTPUT INSERTED.game_pk
                VALUES ({core_placeholders})
            """
            cur.execute(insert_core_sql, core_values)
            game_pk = cur.fetchone()[0]

            # Insert into game_text
            insert_text_sql = """
                INSERT INTO dbo.game_text (game_pk, pgn_san, pgn_movetext_full, uci_seq)
                VALUES (?, ?, ?, ?)
            """
            cur.execute(insert_text_sql, (
                game_pk,
                text_row["pgn_san"],
                text_row["pgn_movetext_full"],
                text_row.get("uci_seq"),
            ))

            conn.commit()
            return game_pk

        except pyodbc.IntegrityError as e:
            # Duplicate (hash_loose): ignore
            conn.rollback()
            if "ux_game_hash_loose" in str(e):
                return None
            raise
