import hashlib
import hmac
import os

import mysql.connector
from mysql.connector import Error

DB_NAME = "apale_space_invaders_db"

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",
}


def _connect(with_database=True):
    try:
        config = dict(DB_CONFIG)

        if with_database:
            config["database"] = DB_NAME

        connection = mysql.connector.connect(**config)

        if connection.is_connected():
            return connection

    except Error as error:
        print(f"Database Connection Error: {error}")

    return None


def create_connection():
    return _connect(True)


def get_db_connection():
    return _connect(True)


def setup_database():
    conn = _connect(False)

    if not conn:
        return False

    cursor = conn.cursor()

    try:
        cursor.execute(
            f"CREATE DATABASE IF NOT EXISTS {DB_NAME} "
            "CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci"
        )
        cursor.execute(f"USE {DB_NAME}")

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS players (
                player_id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(50) NOT NULL UNIQUE,
                password VARCHAR(255) NOT NULL,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS scores (
                score_id INT AUTO_INCREMENT PRIMARY KEY,
                player_id INT NOT NULL,
                score INT NOT NULL DEFAULT 0,
                `level` INT NOT NULL DEFAULT 1,
                date_added TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (player_id)
                    REFERENCES players(player_id)
                    ON DELETE CASCADE
            )
            """
        )

        cursor.execute("SHOW COLUMNS FROM scores LIKE 'level'")

        if not cursor.fetchone():
            cursor.execute(
                "ALTER TABLE scores ADD COLUMN `level` INT NOT NULL DEFAULT 1"
            )

        conn.commit()
        return True

    except Error as error:
        print(f"Database Setup Error: {error}")
        return False

    finally:
        cursor.close()
        conn.close()


def _hash_password(password, salt=None):
    salt = salt or os.urandom(16).hex()

    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        bytes.fromhex(salt),
        120000,
    ).hex()

    return f"{salt}${digest}"


def _verify_password(password, stored):
    try:
        salt, digest = stored.split("$", 1)
    except (ValueError, AttributeError):
        return False

    check = _hash_password(password, salt).split("$", 1)[1]

    return hmac.compare_digest(check, digest)


def register_player(username, password):
    conn = _connect(True)

    if not conn:
        return False, "DATABASE CONNECTION FAILED"

    cursor = conn.cursor()

    try:
        cursor.execute(
            "SELECT player_id FROM players WHERE username = %s",
            (username,),
        )

        if cursor.fetchone():
            return False, "USERNAME ALREADY EXISTS"

        cursor.execute(
            "INSERT INTO players (username, password) VALUES (%s, %s)",
            (username, _hash_password(password)),
        )

        conn.commit()
        return True, "ACCOUNT CREATED"

    except Error as error:
        conn.rollback()
        print(f"Registration Error: {error}")
        return False, "DATABASE ERROR"

    finally:
        cursor.close()
        conn.close()


def login_player(username, password):
    conn = _connect(True)

    if not conn:
        return None, "DATABASE CONNECTION FAILED"

    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT player_id, username, password
            FROM players
            WHERE username = %s
            """,
            (username,),
        )

        player = cursor.fetchone()

        if not player:
            return None, "ACCOUNT NOT FOUND"

        if not _verify_password(password, player["password"]):
            return None, "WRONG PASSWORD"

        player.pop("password", None)
        return player, "OK"

    except Error as error:
        print(f"Login Error: {error}")
        return None, "DATABASE ERROR"

    finally:
        cursor.close()
        conn.close()


def update_username(player_id, new_username):
    conn = _connect(True)

    if not conn:
        return False, "DATABASE CONNECTION FAILED"

    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT player_id FROM players
            WHERE username = %s AND player_id != %s
            """,
            (new_username, player_id),
        )

        if cursor.fetchone():
            return False, "USERNAME ALREADY EXISTS"

        cursor.execute(
            "UPDATE players SET username = %s WHERE player_id = %s",
            (new_username, player_id),
        )

        conn.commit()
        return True, "USERNAME UPDATED"

    except Error as error:
        conn.rollback()
        print(f"Profile Error: {error}")
        return False, "DATABASE ERROR"

    finally:
        cursor.close()
        conn.close()


def delete_player(player_id):
    conn = _connect(True)

    if not conn:
        return False

    cursor = conn.cursor()

    try:
        cursor.execute(
            "DELETE FROM players WHERE player_id = %s", (player_id,)
        )
        conn.commit()
        return True

    except Error as error:
        conn.rollback()
        print(f"Delete Error: {error}")
        return False

    finally:
        cursor.close()
        conn.close()


def save_score(player_id, score, level=1):
    conn = _connect(True)

    if not conn:
        return False

    cursor = conn.cursor()

    try:
        cursor.execute(
            "INSERT INTO scores (player_id, score, `level`) "
            "VALUES (%s, %s, %s)",
            (player_id, score, level),
        )
        conn.commit()
        return True

    except Error as error:
        conn.rollback()
        print(f"Score Error: {error}")
        return False

    finally:
        cursor.close()
        conn.close()


def load_leaderboard(limit=10):
    conn = _connect(True)

    if not conn:
        return []

    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT p.player_id, p.username, s.score, s.`level`, s.date_added
            FROM players p
            INNER JOIN scores s
                ON s.score_id = (
                    SELECT s2.score_id
                    FROM scores s2
                    WHERE s2.player_id = p.player_id
                    ORDER BY s2.score DESC, s2.date_added DESC
                    LIMIT 1
                )
            ORDER BY s.score DESC, s.date_added ASC
            LIMIT %s
            """,
            (limit,),
        )

        return cursor.fetchall()

    except Error as error:
        print(f"Leaderboard Error: {error}")
        return []

    finally:
        cursor.close()
        conn.close()


def get_player_highest_score(player_id):
    return get_player_stats(player_id)["highest"]


def get_player_stats(player_id):
    stats = {"highest": 0, "games": 0, "total": 0, "level": 0}

    conn = _connect(True)

    if not conn:
        return stats

    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT COALESCE(MAX(score), 0),
                   COUNT(*),
                   COALESCE(SUM(score), 0),
                   COALESCE(MAX(`level`), 0)
            FROM scores
            WHERE player_id = %s
            """,
            (player_id,),
        )

        row = cursor.fetchone()

        if row:
            stats["highest"] = int(row[0])
            stats["games"] = int(row[1])
            stats["total"] = int(row[2])
            stats["level"] = int(row[3])

    except Error as error:
        print(f"Stats Error: {error}")

    finally:
        cursor.close()
        conn.close()

    return stats


def get_player_rank(player_id):
    conn = _connect(True)

    if not conn:
        return None

    cursor = conn.cursor()

    try:
        cursor.execute(
            "SELECT MAX(score) FROM scores WHERE player_id = %s",
            (player_id,),
        )

        row = cursor.fetchone()

        if not row or row[0] is None:
            return None

        cursor.execute(
            """
            SELECT COUNT(*) + 1
            FROM (
                SELECT MAX(score) AS best
                FROM scores
                GROUP BY player_id
            ) t
            WHERE t.best > %s
            """,
            (row[0],),
        )

        return int(cursor.fetchone()[0])

    except Error as error:
        print(f"Rank Error: {error}")
        return None

    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    if setup_database():
        print("DATABASE READY")
    else:
        print("DATABASE SETUP FAILED")