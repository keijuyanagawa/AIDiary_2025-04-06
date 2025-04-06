# init_db.py
import sqlite3
from auth import hash_password # auth.py からインポート
import os # osモジュールを追加

DB_NAME = "diary_app.db"

def initialize_database():
    """データベースファイルを初期化し、必要なテーブルを作成し、テストユーザーを追加する"""
    print("[init_db] initialize_database() 開始") # 開始ログ
    conn = None # 接続オブジェクトを初期化
    cursor = None # カーソルオブジェクトも初期化
    try:
        print(f"[init_db] データベース '{DB_NAME}' に接続試行...")
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        print("[init_db] データベース接続成功。")

        # users テーブルの作成
        print("[init_db] users テーブル作成試行...")
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)
        print("[init_db] users テーブル作成/確認完了。")

        # entries テーブルの作成
        print("[init_db] entries テーブル作成試行...")
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
        print("[init_db] entries テーブル作成/確認完了。")

        # emotions テーブルの作成
        print("[init_db] emotions テーブル作成試行...")
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
        print("[init_db] emotions テーブル作成/確認完了。")

        conn.commit()
        print(f"[init_db] テーブル作成コミット完了。")

        # --- テストユーザーの追加 ---
        print("[init_db] テストユーザー追加試行...")
        try:
            test_username = "testuser"
            test_password = "password123"
            hashed_password = hash_password(test_password)

            # ユーザーを挿入 (既に存在する場合は無視する)
            cursor.execute('''
                INSERT OR IGNORE INTO users (username, password_hash)
                VALUES (?, ?)
            ''', (test_username, hashed_password))
            conn.commit()
            print(f"[init_db] テストユーザー '{test_username}' を作成/確認＆コミット完了。")
        except ImportError:
            print("[init_db] エラー: auth.py または hash_password関数が見つかりません。")
        except sqlite3.Error as e:
            print(f"[init_db] テストユーザー作成中にデータベースエラー: {e}")
        except Exception as e:
            print(f"[init_db] テストユーザー作成中に予期せぬエラー: {e}")

    except sqlite3.Error as e:
        print(f"[init_db] データベース処理中にエラー: {e}") # DB関連エラーをキャッチ
    except Exception as e:
        print(f"[init_db] initialize_database内で予期せぬエラー: {e}") # その他のエラー
    finally:
        if conn:
            print("[init_db] データベース接続を閉じます。")
            conn.close()
        else:
            print("[init_db] データベース接続が確立されなかったため、閉じられません。")
        print("[init_db] initialize_database() 終了")

# スクリプトとして直接実行された場合にも動作するように
if __name__ == "__main__":
    print("init_db.py を直接実行しています...")
    initialize_database()
    print("データベースの初期化が完了しました。")
