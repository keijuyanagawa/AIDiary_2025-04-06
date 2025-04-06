# add_dummy_data.py
import db
from datetime import date

# --- 設定 ---
user_id_to_add = 1 # データを入れたいユーザーのID (testuser の ID)

# 追加したいダミーの日記データ (複数追加可能)
dummy_entries = [
    {
        "entry_date": date(2024, 10, 25), # 過去の日付
        "chat_log": "AI: こんにちは！今日はどんな一日でしたか？\nあなた: まあまあでした。\nAI: そうでしたか。何か特別なことはありましたか？\nあなた: 特にないです。",
        "summary": "特に大きな出来事はなかったが、穏やかな一日。",
        "emotions": {'joy': 50, 'anger': 5, 'sadness': 15, 'anxiety': 10, 'relief': 20}
    },
    {
        "entry_date": date(2024, 11, 26), # 過去の日付
        "chat_log": "AI: 今日はどんな感じでしたか？\nあなた: 良い一日でした！\nAI: それは良かったです！何か嬉しいことが？\nあなた: 新しいカフェを見つけました。",
        "summary": "新しい発見があり、満足感のある一日だった。",
        "emotions": {'joy': 80, 'anger': 0, 'sadness': 5, 'anxiety': 5, 'relief': 10}
    },
    {
        "entry_date": date(2024, 12, 27), # 過去の日付
        "chat_log": "AI: 今日の調子はどうですか？\nあなた: ちょっと疲れました。\nAI: お疲れ様です。ゆっくり休んでくださいね。\nあなた: ありがとう。",
        "summary": "少し疲労感があるものの、無事に一日を終えた。",
        "emotions": {'joy': 30, 'anger': 10, 'sadness': 25, 'anxiety': 20, 'relief': 15}
    },
     { # さらに追加する場合
        "entry_date": date(2025, 1, 20),
        "chat_log": "...",
        "summary": "昔の日記のテスト",
        "emotions": {'joy': 60, 'anger': 20, 'sadness': 5, 'anxiety': 5, 'relief': 10}
    },
]
# --- 設定ここまで ---

print("--- ダミーデータ追加開始 ---")
added_count = 0
skipped_count = 0

for entry_data in dummy_entries:
    entry_date_str = entry_data["entry_date"].isoformat()
    print(f"{entry_date_str} のデータを追加試行...")

    # 同じユーザーIDと日付のエントリが既に存在しないか簡易チェック
    # (厳密ではないが、重複エラーを防ぐため)
    existing_entries = db.get_entry_list_by_user(user_id_to_add)
    is_duplicate = any(e['entry_date'] == entry_date_str for e in existing_entries)

    if not is_duplicate:
        entry_id = db.create_entry_and_emotions(
            user_id=user_id_to_add,
            entry_date=entry_data["entry_date"],
            chat_log=entry_data["chat_log"],
            summary=entry_data["summary"],
            emotions=entry_data["emotions"]
        )
        if entry_id:
            print(f"  -> 成功 (Entry ID: {entry_id})")
            added_count += 1
        else:
            print(f"  -> 失敗 (DBエラー)")
            skipped_count += 1
    else:
        print(f"  -> スキップ (同じ日付のエントリが存在)")
        skipped_count += 1

print("--- ダミーデータ追加完了 ---")
print(f"追加: {added_count}件, スキップ/失敗: {skipped_count}件") 