# auth.py
import bcrypt

def hash_password(password):
    """パスワードをハッシュ化する"""
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password_bytes, salt)
    return hashed_password.decode('utf-8') # DB保存用に文字列で返す

def verify_password(plain_password, hashed_password):
    """入力されたパスワードがハッシュと一致するか検証する"""
    plain_password_bytes = plain_password.encode('utf-8')
    hashed_password_bytes = hashed_password.encode('utf-8')
    try:
        # ハッシュ値が bcrypt 形式でない場合にエラーになる可能性を考慮
        if not hashed_password or not hashed_password.startswith('$2b$'):
             print("警告: 無効な形式のハッシュ値です。")
             return False
        return bcrypt.checkpw(plain_password_bytes, hashed_password_bytes)
    except ValueError as e:
        # ハッシュ形式が不正な場合などに ValueError が発生することがある
        print(f"パスワード検証中にエラーが発生しました: {e}")
        return False
    except Exception as e:
        print(f"パスワード検証中に予期せぬエラーが発生しました: {e}")
        return False