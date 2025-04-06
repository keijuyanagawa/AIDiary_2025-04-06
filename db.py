# db.py
import sqlite3
from datetime import date
import pandas as pd

DB_NAME = "diary_app.db"

def get_db_connection():
    """データベース接続を取得する"""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row # 列名でアクセスできるようにする
    return conn

def create_user(username, password_hash):
    """新しいユーザーをデータベースに登録する"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (username, password_hash))
        conn.commit()
        return True # 成功
    except sqlite3.IntegrityError:
        # UNIQUE 制約違反 (ユーザー名が既に存在する)
        print(f"ユーザー名 '{username}' は既に使用されています。")
        return False # 失敗
    except sqlite3.Error as e:
        print(f"ユーザー作成中にデータベースエラーが発生しました: {e}")
        return False # 失敗
    finally:
        conn.close()

def get_user_by_username(username):
    """ユーザー名でユーザー情報を取得する"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()
    if user:
        return dict(user) # sqlite3.Row を dict に変換して返す
    else:
        return None # 見つからない場合は None

def create_entry_and_emotions(user_id, entry_date, chat_log, summary, emotions):
    """
    日記エントリーと感情スコアをデータベースに保存する。
    トランザクション内で実行し、どちらかの保存に失敗したら両方ロールバックする。
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # 1. entries テーブルに挿入
        cursor.execute("""
            INSERT INTO entries (user_id, entry_date, chat_log, summary)
            VALUES (?, ?, ?, ?)
        """, (user_id, entry_date, chat_log, summary))

        # 挿入されたエントリーのIDを取得
        entry_id = cursor.lastrowid

        # 2. emotions テーブルに挿入
        cursor.execute("""
            INSERT INTO emotions (entry_id, joy, anger, sadness, anxiety, relief)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (entry_id,
              emotions.get('joy', 0),
              emotions.get('anger', 0),
              emotions.get('sadness', 0),
              emotions.get('anxiety', 0),
              emotions.get('relief', 0)))

        conn.commit()
        print(f"日記エントリー (ID: {entry_id}) と感情スコアが正常に保存されました。")
        return entry_id

    except sqlite3.Error as e:
        print(f"データベースへの保存中にエラーが発生しました: {e}")
        conn.rollback() # エラーが発生したら変更を元に戻す
        return None
    finally:
        conn.close()

def get_emotions_by_user(user_id):
    """
    指定されたユーザーIDの全ての日記エントリーに対応する感情データを取得し、
    日付順にソートされた Pandas DataFrame として返す。
    """
    conn = get_db_connection()
    query = """
        SELECT
            e.entry_date,
            em.joy,
            em.anger,
            em.sadness,
            em.anxiety,
            em.relief
        FROM emotions em
        JOIN entries e ON em.entry_id = e.id
        WHERE e.user_id = ?
        ORDER BY e.entry_date ASC
    """
    try:
        df = pd.read_sql_query(query, conn, params=(user_id,))
        if not df.empty:
            df['entry_date'] = pd.to_datetime(df['entry_date'])
        print(f"ユーザーID {user_id} の感情データを {len(df)} 件取得しました。")
        return df
    except Exception as e:
        print(f"感情データの取得中にエラーが発生しました: {e}")
        return pd.DataFrame(columns=['entry_date', 'joy', 'anger', 'sadness', 'anxiety', 'relief'])
    finally:
        if conn:
            conn.close()

def get_entry_list_by_user(user_id):
    """
    指定されたユーザーIDの日記エントリーのリスト（IDと日付）を日付の降順で取得する。
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    entries = []
    try:
        cursor.execute("""
            SELECT id, entry_date
            FROM entries
            WHERE user_id = ?
            ORDER BY entry_date DESC
        """, (user_id,))
        entries = [{'id': row['id'], 'entry_date': row['entry_date']} for row in cursor.fetchall()]
        print(f"ユーザーID {user_id} の日記リストを {len(entries)} 件取得しました。")
    except sqlite3.Error as e:
        print(f"日記リストの取得中にエラーが発生しました: {e}")
    finally:
        conn.close()
    return entries

def get_entry_details(entry_id):
    """
    指定されたエントリーIDの日記詳細情報（エントリー内容と感情スコア）を取得する。
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    details = None
    try:
        cursor.execute("""
            SELECT
                e.id, e.user_id, e.entry_date, e.chat_log, e.summary,
                em.joy, em.anger, em.sadness, em.anxiety, em.relief
            FROM entries e
            JOIN emotions em ON e.id = em.entry_id
            WHERE e.id = ?
        """, (entry_id,))
        row = cursor.fetchone()
        if row:
            details = dict(row)
            print(f"エントリーID {entry_id} の詳細を取得しました。")
        else:
            print(f"エントリーID {entry_id} の詳細が見つかりませんでした。")
    except sqlite3.Error as e:
        print(f"日記詳細の取得中にエラーが発生しました: {e}")
    finally:
        conn.close()
    return details