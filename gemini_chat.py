# gemini_chat.py
import google.generativeai as genai
import os
import json
from dotenv import load_dotenv

# .envファイルから環境変数を読み込む
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    # アプリケーション実行時にエラーを出すよりは、ログ等で通知する方が良いかも
    print("警告: 環境変数 'GEMINI_API_KEY' が設定されていません。API連携は失敗します。")
    # raise ValueError("環境変数 'GEMINI_API_KEY' が設定されていません。") # 起動時に落とす場合

# Gemini API の設定
try:
    genai.configure(api_key=API_KEY)
    # Safety settings を調整 (開発用、本番では要検討)
    safety_settings = [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
    ]
    model = genai.GenerativeModel('gemini-1.5-flash', safety_settings=safety_settings)
except Exception as e:
    print(f"Gemini APIの設定中にエラーが発生しました: {e}")
    # エラー発生時も model オブジェクトがない状態になるため、以降の呼び出しでエラーになる
    model = None # model が None であることで以降の処理で API 不可を判定できる


def get_chat_response(prompt, chat_history):
    """
    ユーザーのプロンプトと会話履歴を受け取り、AIの応答を返す。
    Args:
        prompt (str): ユーザーからの最新の入力 (実際には履歴の最後)。
        chat_history (list): これまでの会話履歴のリスト。
    Returns:
        str: AIからの応答テキスト。
        list: 更新された会話履歴。
    """
    if not model:
        return "エラー: Gemini APIが設定されていません。", chat_history

    try:
        # 履歴全体をコンテキストとして応答を生成 (履歴は app.py で管理・更新)
        # chat_history は get する時点での完全な履歴のはず
        print(f"DEBUG: Sending history to Gemini: {chat_history}") # デバッグ用
        response = model.generate_content(chat_history) # 履歴全体を渡す

        ai_response = response.text
        # AIの応答を履歴に追加 (これは呼び出し元の app.py で行うべき)
        # chat_history.append({'role':'model', 'parts': [ai_response]}) # ここでは変更しない

        print(f"DEBUG: Received response from Gemini: {ai_response}") # デバッグ用
        return ai_response, chat_history # 応答テキストと、変更前の履歴を返す

    except Exception as e:
        print(f"Gemini API チャット呼び出し中にエラーが発生しました: {e}")
        if hasattr(e, 'response'): print("エラーレスポンス詳細:", e.response)
        return f"AI応答の取得中にエラーが発生しました: {e}", chat_history

def analyze_diary_entry(full_chat_log_text):
    """
    チャットログ全体を受け取り、要約と感情分析を行い、結果を辞書で返す。
    """
    if not model:
        print("エラー: Gemini APIが設定されていません。分析を実行できません。")
        return None, None

    prompt = f"""
以下のチャットログを分析し、以下の2つの要素を含むJSON形式で結果を返してください。

1.  **summary**: チャットログの内容を簡潔に要約した日記風の文章。ユーザーの発言を中心にまとめてください。
2.  **emotions**: チャットログ全体から読み取れる以下の5つの感情について、ユーザーの感情を中心に、それぞれ0から100の整数値でスコアを付けたオブジェクト。スコアが低い感情も含めて必ず5つ全て記述してください。
    *   joy (喜び)
    *   anger (怒り)
    *   sadness (悲しみ)
    *   anxiety (不安)
    *   relief (安堵)

期待するJSON形式の例:
{{
  "summary": "今日は新しいカフェに行き、コーヒーも美味しく店員さんも親切で嬉しかった。帰りに少し雨に降られたのは残念だったが、全体的には良い一日だったと感じている。",
  "emotions": {{
    "joy": 75,
    "anger": 5,
    "sadness": 25,
    "anxiety": 15,
    "relief": 40
  }}
}}

--- 分析対象チャットログ ---
{full_chat_log_text}
--- ここまで ---

JSON形式の出力のみを生成してください。他の説明文は不要です。
"""
    print("Gemini APIに分析リクエストを送信中...")
    try:
        # JSONモードを試す場合:
        # response = model.generate_content(prompt, generation_config=genai.types.GenerationConfig(response_mime_type="application/json"))
        response = model.generate_content(prompt)

        response_text = response.text.strip()
        if response_text.startswith("```json"):
            response_text = response_text[7:].strip()
        if response_text.endswith("```"):
            response_text = response_text[:-3].strip()

        result_data = json.loads(response_text)
        summary = result_data.get("summary")
        emotions = result_data.get("emotions")

        # より厳密なバリデーション
        required_emotions = {'joy', 'anger', 'sadness', 'anxiety', 'relief'}
        if isinstance(summary, str) and summary.strip() and \
           isinstance(emotions, dict) and required_emotions.issubset(emotions.keys()) and \
           all(isinstance(emotions[key], int) and 0 <= emotions[key] <= 100 for key in required_emotions):
            # 不要なキーが含まれていても許容するが、必要な5つは必須とする
            valid_emotions = {key: emotions[key] for key in required_emotions}
            print("分析成功:", summary, valid_emotions)
            return summary, valid_emotions
        else:
            print("エラー: 取得したJSONの形式または内容が不正です。")
            print("受け取ったデータ:", result_data)
            return None, None

    except json.JSONDecodeError as json_e:
        print(f"エラー: Geminiからの応答が期待したJSON形式ではありませんでした。")
        print(f"エラー詳細: {json_e}")
        print("--- 受け取ったテキスト ---")
        print(response.text)
        return None, None
    except Exception as e:
        print(f"Gemini APIの分析呼び出し中にエラーが発生しました: {e}")
        if hasattr(e, 'response'): print("エラーレスポンス詳細:", e.response)
        return None, None