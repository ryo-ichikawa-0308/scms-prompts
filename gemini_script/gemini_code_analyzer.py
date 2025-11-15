import sys
import configparser
import json
import time
from pathlib import Path
from google import genai
from google.genai.errors import APIError
from typing import Dict, Any, List
import mimetypes

# --- 設定ファイル名とパス ---
API_INI = 'api.ini'
SETTING_INI = 'setting.ini'
INPUTS_JSON = 'inputs.json'

def load_settings() -> Dict[str, Any]:
    """各種初期情報（APIキー、設定、入力定義）を読み込む"""
    settings: Dict[str, Any] = {}
    current_dir = Path(__file__).resolve().parent
    
    api_ini_path = current_dir / API_INI
    setting_ini_path = current_dir / SETTING_INI
    inputs_json_path = current_dir / INPUTS_JSON
    config = configparser.ConfigParser()

    # 1. api.iniからAPIキーを読み込む
    try:
        read_files = config.read(str(api_ini_path), encoding='utf-8')
        
        if not read_files:
            raise FileNotFoundError(f"ファイルが見つからないか、読み込めません: {api_ini_path.resolve()}")

        if 'GEMINI' in config:
            api_key = config['GEMINI'].get('API_KEY')
        else:
            raise ValueError("API_KEYが [GEMINI] セクションに見つかりません。")

        settings['api_key'] = api_key.strip()
        
    except Exception as e:
        print(f"エラー: {API_INI} の読み込み中にエラーが発生しました: {e}")
        raise

    # 2. setting.iniから設定値を読み込む
    try:
        config.read(setting_ini_path, encoding='utf-8')
        settings['try_times'] = config.getint('SETTING', 'TRY_TIMES', fallback=1)
        settings['interval'] = config.getfloat('SETTING', 'INTERVAL', fallback=5.0)
        settings['dist'] = Path(config.get('SETTING', 'DIST', fallback='output'))
        settings['model'] = config.get('SETTING', 'MODEL', fallback='gemini-2.5-flash')
    except configparser.Error as e:
        print(f"エラー: {SETTING_INI} の解析中にエラーが発生しました: {e}")
        raise

    # 3. inputs.jsonからプロンプトとファイル定義を読み込む (構造変更)
    try:
        with open(inputs_json_path, 'r', encoding='utf-8') as f:
            inputs_data = json.load(f)
        
        # 'prompt' はメインプロンプト
        settings['prompt_path'] = Path(inputs_data.get('prompt', ''))
        # 'context_files' は学習/コンテキストとして使うファイル群
        settings['context_files'] = [Path(p) for p in inputs_data.get('context_files', [])]
        # 'output_file_name' は結果を書き出すファイル名
        settings['output_file_name'] = inputs_data.get('output_file_name', 'gemini_response.txt')
        
        if not settings['prompt_path'].name:
            raise ValueError("inputs.jsonに 'prompt' のパスが指定されていません。")

    except Exception as e:
        print(f"エラー: {INPUTS_JSON} の読み込みまたは解析中にエラーが発生しました: {e}")
        raise

    return settings

def read_prompt_file(settings: Dict[str, Any]) -> str:
    """プロンプトファイルを読み込む"""
    prompt_path = settings['prompt_path']
    try:
        with open(prompt_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"エラー: プロンプトファイル {prompt_path} が見つかりません。")
        raise
    except Exception as e:
        print(f"エラー: プロンプトファイルの読み込み中にエラーが発生しました: {e}")
        raise

def upload_files(client: genai.Client, file_paths: List[Path]) -> List[genai.files]:
    """指定されたファイルをアップロードし、Fileオブジェクトのリストを返す"""
    uploaded_files: List[genai.files] = []
    for path in file_paths:
        if not path.is_file():
            print(f"警告: ファイル {path} が見つかりません。スキップします。")
            continue
        try:
            # MIMEタイプを推測
            guessed_mime_type = mimetypes.guess_type(path)[0]
            
            # --- MIMEタイプ決定ロジック ---
            # 1. デフォルトを 'text/plain' に設定
            mime_type = 'text/plain' 
            
            if guessed_mime_type:
                # 2. 特定のサポートテキスト形式（そのまま維持）
                if guessed_mime_type == 'text/markdown' or \
                   guessed_mime_type == 'application/json':
                    mime_type = guessed_mime_type
                
                # 3. バイナリ形式（そのまま維持）
                elif guessed_mime_type.startswith('image/') or \
                     guessed_mime_type.startswith('audio/') or \
                     guessed_mime_type.startswith('video/') or \
                     guessed_mime_type == 'application/pdf':
                    mime_type = guessed_mime_type
                
                # 4. その他の全てのタイプ（text/vnd.trolltech.linguistなどの非サポートタイプを含む）は 'text/plain' に強制
                else:
                    if guessed_mime_type != 'text/plain':
                        print(f"警告: 推測されたMIMEタイプ '{guessed_mime_type}' は 'text/plain' として扱われます。")
                    mime_type = 'text/plain'
            # --- MIMEタイプ決定ロジック終了 ---
            
            print(f"ファイルをアップロード中: {path.name} (MIME: {mime_type})...")
            
            uploaded_file = None
            
            # --- 試行1: config引数を使用してmime_typeを渡す (推奨形式) ---
            try:
                uploaded_file = client.files.upload(
                    file=str(path),
                    config={"mime_type": mime_type} 
                )
            except TypeError as e:
                # config引数が予期しない場合や、config内部のキーエラーの場合
                if "unexpected keyword argument 'config'" in str(e) or "mime_type" in str(e):
                    print("警告: config引数またはその内部キーでエラーが発生しました。トップレベル引数なしで再試行します...")
                    
                    # --- 試行2: config引数なしで再試行 (古い/一部バージョン) ---
                    uploaded_file = client.files.upload(
                        file=str(path)
                    )
                else:
                    # その他のTypeErrorは再スロー
                    raise 

            if uploaded_file:
                uploaded_files.append(uploaded_file)
                print(f"アップロード完了: {uploaded_file.name} ({uploaded_file.display_name})")
            else:
                # 試行2でもuploaded_fileがNoneの場合
                raise Exception("ファイルアップロードに失敗しました (uploaded_file is None)")

        except Exception as e:
            # その他のAPIエラーやファイルエラーなど
            print(f"エラー: ファイル {path.name} のアップロード中に致命的なエラーが発生しました: {e}")
            raise
    return uploaded_files

def delete_uploaded_files(client: genai.Client, files: List[genai.files]):
    """アップロードされたファイルをAPIから削除する"""
    print("アップロードされたファイルをクリーンアップ中...")
    for file in files:
        try:
            client.files.delete(name=file.name)
            print(f"削除成功: {file.name}")
        except Exception as e:
            print(f"警告: ファイル {file.name} の削除中にエラーが発生しました: {e}")


def run_chat_analysis(main_prompt: str, analysis_file_path: Path, settings: Dict[str, Any]):
    """Gemini APIを呼び出し、チャットセッションを利用して解析を行う"""
    
    client = genai.Client(api_key=settings['api_key'])
    model = settings['model']
    uploaded_files: List[genai.File] = []
    
    try:
        # 1. 学習ファイルをアップロード (context_files)
        context_files = settings['context_files']
        uploaded_context_files = upload_files(client, context_files)
        uploaded_files.extend(uploaded_context_files)
        
        # 2. 解析用ファイルをアップロード (analysis_file)
        uploaded_analysis_file = upload_files(client, [analysis_file_path])
        if not uploaded_analysis_file:
            raise FileNotFoundError(f"解析用ファイル {analysis_file_path} のアップロードに失敗しました。")
        uploaded_files.extend(uploaded_analysis_file)

        # Chat Sessionの初期化メッセージ (学習ファイルと最初のプロンプトを結合)
        initial_history_parts = []
        if uploaded_context_files:
            # === 修正部分: Fileオブジェクトを Part 辞書形式に明示的に変換する ===
            for file in uploaded_context_files:
                # Fileオブジェクトから name と mime_type を取得し、fileData 構造を作成
                initial_history_parts.append({
                    "fileData": {
                        "mimeType": file.mime_type,
                        # Fileオブジェクトの name (リソースパス) を URI として使用
                        "fileUri": file.name 
                    }
                }) 
            
            # テキストパートを明示的に辞書形式（{"text": "..."}）でラップする
            initial_history_parts.append({
                "text": "上記のファイルは、私が使用しているプロジェクトのコンテキストとコーディング規約です。これらを参考にして応答してください。"
            })
            
            # Chat Sessionを作成し、初期コンテキストとして学習ファイルを送信
            print("Chat Sessionを作成し、学習コンテキストを登録中...")
            chat = client.chats.create(
                model=model,
                history=[{
                    "role": "user",
                    "parts": initial_history_parts
                }]
            )

            # モデルの応答を待ってから次のメッセージを送信
            # この応答は通常スキップされますが、Chat Sessionの動作として必要です
            _ = chat.get_history()
            
        else:
            # 学習ファイルがない場合は、空のChat Sessionを作成
            print("学習ファイルがないため、空のChat Sessionを作成します。")
            chat = client.chats.create(model=model)

        # 3. 解析依頼メッセージの作成と送信
        print(f"解析用ファイル {analysis_file_path.name} を含めて解析依頼を送信中...")
        
        # 解析依頼のプロンプト（テキスト + 解析用ファイル）
        analysis_parts = [
            uploaded_analysis_file[0], # 解析用ファイル
            f"このファイル（{analysis_file_path.name}）を解析し、以下のプロンプトに従って結果を生成してください:\n\n{main_prompt}"
        ]

        # API呼び出しと再試行ロジック
        response = None
        for attempt in range(settings['try_times']):
            try:
                print(f"API呼び出し試行回数: {attempt + 1}/{settings['try_times']}")
                response = chat.send_message(analysis_parts)
                break
            except APIError as e:
                print(f"APIエラーが発生しました: {e}")
                if attempt < settings['try_times'] - 1:
                    print(f"{settings['interval']}秒待機してから再試行します。")
                    time.sleep(settings['interval'])
                else:
                    print("再試行回数を超過しました。処理を終了します。")
                    raise
            except Exception as e:
                print(f"予期せぬエラーが発生しました: {e}")
                raise

        if response is None:
            raise Exception("APIからの応答が得られませんでした。")

        return response.text

    finally:
        # 4. クリーンアップ
        delete_uploaded_files(client, uploaded_files)


def write_output(response_text: str, output_file_name: str, settings: Dict[str, Any]):
    """API応答テキストを単一ファイルとして出力する"""
    dist_dir = settings['dist']
    dist_dir.mkdir(parents=True, exist_ok=True)
    
    # ファイル名から危険な文字を除去
    safe_output_file_name = output_file_name.replace('/', '_').replace('\\', '_').replace('..', '')
    output_path = dist_dir / safe_output_file_name
    
    print(f"結果をファイル {output_path.resolve()} に出力します。")

    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(response_text)
        print(f"ファイル出力成功: {output_path.name}")
    except Exception as e:
        print(f"エラー: ファイル {output_path} の書き込み中にエラーが発生しました: {e}")
        raise


def main():
    """メイン処理"""
    # コマンドライン引数チェック
    if len(sys.argv) < 2:
        print("エラー: 解析対象のファイルパスが引数として指定されていません。")
        print("使用法: python gemini_code_analyzer.py <解析対象のファイルパス>")
        sys.exit(1)

    analysis_file_path = Path(sys.argv[1])
    if not analysis_file_path.is_file():
        print(f"エラー: 指定されたファイルが見つかりません: {analysis_file_path.resolve()}")
        sys.exit(1)

    try:
        # 1. 各種初期情報の読み込み
        settings = load_settings()
        
        # 2. プロンプトファイルの読み込み
        main_prompt = read_prompt_file(settings)
        
        # 3. API処理 (Chat Sessionの初期化、ファイルのアップロードと送信)
        response_text = run_chat_analysis(main_prompt, analysis_file_path, settings)
        
        # 4. 結果のファイル出力
        write_output(response_text, settings['output_file_name'], settings)
        
        print("\n✅ 全ての処理が完了しました。")

    except Exception as e:
        print(f"\n❌ スクリプトの実行中に致命的なエラーが発生しました: {e}")
        # スクリプトをエラー終了させる
        sys.exit(1)

if __name__ == '__main__':
    # Google GenAI SDKのログレベルを設定 (デバッグ情報が必要な場合)
    # genai.set_stream_logging(level='DEBUG')
    main()