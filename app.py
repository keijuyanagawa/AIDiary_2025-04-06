# app.py
import streamlit as st
import db
import auth
import gemini_chat
from datetime import date
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# --- セッション状態の初期化 ---
required_keys = {
    'logged_in': False,
    'username': None,
    'user_id': None,
    'chat_history': [],
    'conversation_started': False,
    'selected_diary_id': None
}
for key, default_value in required_keys.items():
    if key not in st.session_state:
        st.session_state[key] = default_value

# --- テスト用ユーザー作成（初回起動時など） ---
# 必要に応じてコメント解除して実行し、ユーザーを作成してください。
# def create_initial_user_if_not_exists(username, password):
#     user = db.get_user_by_username(username)
#     if user is None:
#         print(f"テストユーザー '{username}' が存在しないため作成します...")
#         hashed_password = auth.hash_password(password)
#         if db.create_user(username, hashed_password):
#             print(f"テストユーザー '{username}' を作成しました。")
#         else:
#             print(f"テストユーザー '{username}' の作成に失敗しました。")
# create_initial_user_if_not_exists('testuser', 'password') # 例

# --- ログイン画面 ---
if not st.session_state['logged_in']:
    st.title("AIチャット日記アプリ - ログイン")

    with st.form("login_form"):
        username_input = st.text_input("ユーザー名")
        password_input = st.text_input("パスワード", type="password")
        submitted = st.form_submit_button("ログイン")

        if submitted:
            if not username_input or not password_input:
                st.error("ユーザー名とパスワードを入力してください。")
            else:
                user = db.get_user_by_username(username_input)
                # --- デバッグ出力ここから --- を削除
                # print(f"--- ログイン試行: ユーザー名 '{username_input}' ---")
                # if user:
                #     print(f"データベースからユーザー情報を取得しました: id={user['id']}, username={user['username']}")
                #     # パスワードハッシュが取得できているか確認
                #     if 'password_hash' in user:
                #         print(f"データベースのハッシュ値: {user['password_hash'][:10]}... (先頭10文字)") # ハッシュ全体は表示しない
                #         # パスワード検証を実行
                #         try:
                #             verification_result = auth.verify_password(password_input, user['password_hash'])
                #             print(f"パスワード検証結果 (verify_password): {verification_result}")
                #         except Exception as e:
                #             print(f"verify_password 実行中にエラーが発生しました: {e}")
                #             verification_result = False # エラー時は検証失敗とする
                #     else:
                #         print("エラー: ユーザー情報に password_hash が含まれていません。")
                #         verification_result = False
                # else:
                #     print("データベースでユーザーが見つかりませんでした。")
                #     verification_result = False # ユーザーが見つからないので検証は失敗
                # --- デバッグ出力ここまで --- を削除

                # verify_password に渡す前に user と password_hash が存在するか確認 <-- このコメントは元のロジックのもの
                # 修正: verification_result を直接使うようにする <-- このコメントも不要になる可能性
                # 再度 auth.verify_password を呼び出す形に戻す
                if user and 'password_hash' in user and auth.verify_password(password_input, user['password_hash']):
                    st.session_state['logged_in'] = True
                    st.session_state['username'] = user['username']
                    st.session_state['user_id'] = user['id']
                    # ログイン成功時に状態をリセット
                    st.session_state['chat_history'] = []
                    st.session_state['conversation_started'] = False
                    st.session_state['selected_diary_id'] = None
                    st.success(f"{user['username']} としてログインしました。")
                    st.rerun() # メイン画面へ遷移
                else:
                    st.error("ユーザー名またはパスワードが正しくありません。")

# --- メインアプリケーション画面（ログイン後） ---
else:
    # --- サイドバー ---
    with st.sidebar:
        st.title("メニュー")
        st.write(f"ユーザー: {st.session_state['username']}")
        user_id = st.session_state.get('user_id')

        # 日記選択肢の準備
        diary_options = {None: "✨ 新しい日記を書く"} # Noneをキーに
        if user_id:
            diary_entries = db.get_entry_list_by_user(user_id)
            for entry in diary_entries:
                # 日付が見やすいようにフォーマット（必要なら）
                entry_date_str = entry['entry_date']
                try:
                     # 日付文字列をパースしてフォーマットし直す例（環境によるかも）
                     parsed_date = date.fromisoformat(entry_date_str)
                     entry_date_str = parsed_date.strftime('%Y年%m月%d日') # 例: 2023年10月27日
                except ValueError:
                     pass # パース失敗時は元の文字列を使う
                diary_options[entry['id']] = f"📖 {entry_date_str}" # 絵文字を追加

        # 日記選択セレクトボックス
        # key を使うことで、rerun後も選択状態が維持される
        st.selectbox(
            "過去の日記 / 新規作成",
            options=list(diary_options.keys()),
            format_func=lambda x: diary_options[x],
            key='selected_diary_id' # このキーで選択中のIDが session_state に保存される
        )

        # ログアウトボタン
        if st.button("ログアウト"):
            # セッション情報をクリア
            for key in required_keys.keys(): # 定義したキーを全てクリア
                st.session_state[key] = required_keys[key]
            st.success("ログアウトしました。")
            st.rerun() # ログイン画面へ遷移

    # --- メインエリア ---
    st.title("AIチャット日記")

    # --- 過去の日記詳細表示 ---
    if st.session_state.selected_diary_id is not None:
        selected_id = st.session_state.selected_diary_id
        st.markdown("---")
        st.header(f"{diary_options[selected_id]} の内容") # セレクトボックスの表示名を使う

        entry_details = db.get_entry_details(selected_id)

        if entry_details:
            st.write(f"**日付:** {entry_details['entry_date']}")
            st.write("**AIによる要約:**")
            st.info(entry_details['summary'])

            st.write("**感情スコア:**")
            emotions_to_display = {k: entry_details[k] for k in ['joy', 'anger', 'sadness', 'anxiety', 'relief']}
            cols = st.columns(len(emotions_to_display))
            i = 0
            for emotion, score in emotions_to_display.items():
                with cols[i]:
                    st.metric(label=emotion.capitalize(), value=score)
                i += 1

            with st.expander("チャットログを見る"):
                st.text_area(
                    "ログ", value=entry_details['chat_log'], height=300,
                    disabled=True, key=f"log_{entry_details['id']}"
                )
        else:
            st.error("選択された日記の詳細情報の取得に失敗しました。")
        st.markdown("---")

    # --- 新しい日記の入力 / チャットエリア ---
    # selected_diary_id が None の時だけ表示する方が自然かもしれない
    elif st.session_state.selected_diary_id is None:
        st.header("💬 新しい日記を書く")

        # チャット履歴表示エリア
        chat_container = st.container(height=400)
        with chat_container:
            # 最初のAIからの問いかけ
            if not st.session_state['conversation_started'] and not st.session_state['chat_history']:
                 initial_prompt = "こんにちは！今日はどんな一日でしたか？"
                 st.session_state['chat_history'].append({'role': 'model', 'parts': [initial_prompt]})
                 st.session_state['conversation_started'] = True # 会話開始フラグ

            # 履歴を表示
            for message in st.session_state.get('chat_history', []):
                role = message.get('role')
                text = message.get('parts', [""])[0]
                avatar = "👤" if role == "user" else "🤖"
                with st.chat_message(name=role, avatar=avatar): # nameを'user'/'model'に
                    st.write(text)

        # ユーザー入力
        user_input = st.chat_input("メッセージを入力してください...")

        if user_input:
            # 1. ユーザーのメッセージを履歴に追加
            st.session_state['chat_history'].append({'role': 'user', 'parts': [user_input]})

            # 2. AIの応答を取得 (gemini_chat を呼び出す)
            with st.spinner("AIが応答を考えています..."):
                # 応答取得時には最新の履歴全体を渡す
                ai_response_text, _ = gemini_chat.get_chat_response(
                    user_input, # 最新の入力（これは履歴に含まれているが、念のため渡しても良い）
                    st.session_state['chat_history'] # 最新の履歴
                )

            # 3. AIの応答を履歴に追加
            if ai_response_text and not ai_response_text.startswith("エラー"):
                 st.session_state['chat_history'].append({'role': 'model', 'parts': [ai_response_text]})
            else:
                 # エラーメッセージも履歴に（あるいは st.error で表示）
                 st.session_state['chat_history'].append({'role': 'model', 'parts': [f"エラーが発生しました: {ai_response_text}"]})

            # 4. UIを更新するために再実行
            st.rerun()

        # --- 会話終了と分析・保存ボタン ---
        st.markdown("---")
        analysis_placeholder = st.empty() # 結果表示用プレースホルダ

        # 会話がある程度進んだらボタンを有効化 (例: ユーザーの発言が1回以上あれば)
        can_save = any(msg['role'] == 'user' for msg in st.session_state['chat_history'])

        if st.button("会話を終了して日記を保存する", disabled=not can_save):
            if st.session_state['chat_history']:
                with st.spinner("日記を分析・保存中..."):
                    # 1. ログ整形
                    chat_log_lines = []
                    for msg in st.session_state['chat_history']:
                        role = "あなた" if msg.get('role') == 'user' else "AI"
                        text = msg.get('parts', [""])[0]
                        chat_log_lines.append(f"{role}: {text}")
                    full_chat_log_text = "\n".join(chat_log_lines)

                    # 2. 分析
                    summary, emotions = gemini_chat.analyze_diary_entry(full_chat_log_text)

                    if summary and emotions:
                        # 3. 保存
                        today = date.today()
                        current_user_id = st.session_state.get('user_id')
                        if current_user_id:
                            entry_id = db.create_entry_and_emotions(
                                user_id=current_user_id, entry_date=today,
                                chat_log=full_chat_log_text, summary=summary, emotions=emotions
                            )
                            if entry_id:
                                analysis_placeholder.success("日記を保存しました！")
                                # 保存結果を表示
                                with analysis_placeholder.container():
                                    st.subheader("保存された日記の分析結果")
                                    st.write("**要約:**"); st.write(summary)
                                    st.write("**感情スコア:**")
                                    cols = st.columns(len(emotions))
                                    i = 0
                                    for emo, score in emotions.items():
                                        with cols[i]: st.metric(label=emo.capitalize(), value=score)
                                        i += 1
                                # 状態リセットして rerun
                                st.session_state['chat_history'] = []
                                st.session_state['conversation_started'] = False
                                st.info("新しい日記を始める準備ができました。（ページが更新されます）")
                                # 少し待ってから rerun する方がユーザー体験が良いかも
                                import time; time.sleep(2)
                                st.rerun()
                            else: analysis_placeholder.error("DB保存エラー")
                        else: analysis_placeholder.error("ユーザーIDエラー")
                    else: analysis_placeholder.error("AI分析エラー")
            else:
                st.warning("まだ会話がありません。")

    # --- 感情グラフの表示 (ログイン中なら常に表示) ---
    st.markdown("---")
    st.header("📊 感情の推移グラフ")
    current_user_id_for_graph = st.session_state.get('user_id')
    if current_user_id_for_graph:
        emotion_df = db.get_emotions_by_user(current_user_id_for_graph)
        if not emotion_df.empty:
            try:
                fig, ax = plt.subplots(figsize=(10, 5))
                for emotion in ['joy', 'anger', 'sadness', 'anxiety', 'relief']:
                    if emotion in emotion_df.columns: # 念のためカラム存在確認
                        ax.plot(emotion_df['entry_date'], emotion_df[emotion], marker='o', linestyle='-', label=emotion.capitalize())

                ax.set_title('感情スコアの推移')
                ax.set_xlabel('日付'); ax.set_ylabel('スコア (0-100)')
                ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))
                ax.grid(axis='y', linestyle='--') # Y軸のみグリッド
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d')) # YYYY-MM-DD から MM/DD に変更
                ax.xaxis.set_major_locator(mdates.AutoDateLocator(minticks=3, maxticks=10)) # 目盛り数を自動調整
                fig.autofmt_xdate()
                ax.set_ylim(0, 105)
                plt.tight_layout() # レイアウト調整
                st.pyplot(fig)
                plt.close(fig) # メモリ解放のために閉じる
            except Exception as e:
                st.error(f"グラフの描画中にエラーが発生しました: {e}")
        else:
             st.info("まだ記録された感情データがありません。日記を保存するとグラフが表示されます。")
    # else: # ログインしてない場合は表示されない (メイン画面に入れないため不要)
    #     st.warning("グラフを表示するにはログインしてください。")