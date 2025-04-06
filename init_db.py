# init_db.py
import sqlite3

DB_NAME = "diary_app.db"

def initialize_database():
    """データベースファイルを初期化し、必要なテーブルを作成する"""
    conn = None # 接続オブジェクトを初期化
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        # users テーブルの作成 (もし存在しなければ)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # entries テーブルの作成 (もし存在しなければ)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            entry_date DATE NOT NULL,
            chat_log TEXT NOT NULL,
            summary TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        """)
        # created_at を追加 (後でソート等に使えるかも)

        # emotions テーブルの作成 (もし存在しなければ)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS emotions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entry_id INTEGER NOT NULL,
            joy INTEGER DEFAULT 0,
            anger INTEGER DEFAULT 0,
            sadness INTEGER DEFAULT 0,
            anxiety INTEGER DEFAULT 0,
            relief INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (entry_id) REFERENCES entries (id)
        )
        """)
        # created_at を追加、DEFAULT 0 を設定

        conn.commit()
        print(f"データベース '{DB_NAME}' が初期化され、必要なテーブルが作成/確認されました。")

    except sqlite3.Error as e:
        print(f"データベースエラーが発生しました: {e}")
    finally:
        # --- テストユーザーの追加 ---
        if conn: # connが正常に確立された場合のみ実行
            try:
                from auth import hash_password # auth.py からインポート
                test_username = "testuser"
                test_password = "password123"
                hashed_password = hash_password(test_password)

                # ユーザーを挿入 (既に存在する場合は無視する)
                cursor.execute('''
                    INSERT OR IGNORE INTO users (username, password_hash)
                    VALUES (?, ?)
                ''', (test_username, hashed_password))
                conn.commit()
                print(f"テストユーザー '{test_username}' を作成（または既に存在）しました。")
            except ImportError:
                print("auth.py または hash_password関数が見つかりません。テストユーザーは作成されませんでした。")
            except sqlite3.Error as e:
                print(f"テストユーザー作成中にデータベースエラーが発生しました: {e}")
            except Exception as e:
                print(f"テストユーザー作成中に予期せぬエラーが発生しました: {e}")
            finally:
                 # 接続を閉じる前にテストユーザー関連のエラーが発生してもconn.close()が呼ばれるように
                if conn:
                    conn.close()
        # --- ここまで ---

if __name__ == "__main__":
    initialize_database()