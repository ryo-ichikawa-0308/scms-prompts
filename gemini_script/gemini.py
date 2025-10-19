import configparser
import json
import time
from pathlib import Path
from google import genai
from google.genai.errors import APIError

# --- 設定ファイル名とパス ---
API_INI = 'api.ini'
SETTING_INI = 'setting.ini'
INPUTS_JSON = 'inputs.json'

def load_settings():
    """各種初期情報（APIキー、設定、入力定義）を読み込む"""
    settings = {}
    current_dir = Path(__file__).resolve().parent
    
    api_ini_path = current_dir / API_INI
    setting_ini_path = current_dir / SETTING_INI
    inputs_json_path = current_dir / INPUTS_JSON
    config = configparser.ConfigParser()

    # 1. api.iniからAPIキーを読み込む
    try:
        # INIファイルを読み込む
        read_files = config.read(str(api_ini_path), encoding='utf-8')
        
        if not read_files:
             # configparser.read() はファイルが見つからなかった場合、空のリストを返す
             raise FileNotFoundError(f"ファイルが見つからないか、読み込めません: {api_ini_path.resolve()}")

        if 'GEMINI' in config:
            api_key = config['GEMINI'].get('API_KEY')
        else:
            raise ValueError("API_KEYが [GEMINI] セクションまたはセクションに見つかりません。")

        settings['api_key'] = api_key.strip()
        
    except FileNotFoundError as e:
        print(f"エラー: 設定ファイルが見つかりません。パス: {e.filename}")
        raise
    except configparser.Error as e:
        print(f"エラー: {API_INI} の解析中にエラーが発生しました: {e}")
        raise
    except ValueError as e:
        print(f"エラー: {API_INI} の設定値エラーです: {e}")
        raise
    except Exception as e:
        print(f"エラー: {API_INI} の読み込み中に予期せぬエラーが発生しました: {e}")
        raise

    # 2. setting.iniから設定値を読み込む
    try:
        config.read(setting_ini_path, encoding='utf-8')
        # デフォルトセクションから設定を取得
        default_section = config['SETTING']
        settings['try_times'] = default_section.getint('TRY_TIMES', 1)
        settings['interval'] = default_section.getfloat('INTERVAL', 5.0)
        settings['separator'] = default_section.get('SEPARATOR', '------')
        settings['dist'] = Path(default_section.get('DIST', 'output'))
    except FileNotFoundError:
        print(f"エラー: {SETTING_INI} が見つかりません。")
        raise
    except configparser.Error as e:
        print(f"エラー: {SETTING_INI} の解析中にエラーが発生しました: {e}")
        raise

    # 3. inputs.jsonからプロンプトと入力定義を読み込む
    try:
        with open(inputs_json_path, 'r', encoding='utf-8') as f:
            inputs_data = json.load(f)
        
        settings['prompt_path'] = Path(inputs_data.get('prompt'))
        settings['inputs'] = inputs_data.get('inputs', {})
    except FileNotFoundError:
        print(f"エラー: {INPUTS_JSON} が見つかりません。")
        raise
    except json.JSONDecodeError as e:
        print(f"エラー: {INPUTS_JSON} のJSON解析中にエラーが発生しました: {e}")
        raise

    return settings

def read_prompt_and_replace(settings):
    """プロンプトファイルを読み込み、インプットファイルの内容でプレースホルダを置き換える"""
    
    # 2. プロンプトファイルの読み込み
    prompt_path = settings['prompt_path']
    try:
        with open(prompt_path, 'r', encoding='utf-8') as f:
            prompt_text = f.read()
    except FileNotFoundError:
        print(f"エラー: プロンプトファイル {prompt_path} が見つかりません。")
        raise
    except Exception as e:
        print(f"エラー: プロンプトファイルの読み込み中にエラーが発生しました: {e}")
        raise

    # 3. インプットファイルの読み込みと置き換え
    for placeholder, file_paths in settings['inputs'].items():
        replacement_content = []
        for file_path_str in file_paths:
            file_path = Path(file_path_str)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    replacement_content.append(f.read())
            except FileNotFoundError:
                print(f"警告: インプットファイル {file_path} が見つかりません。スキップします。")
                continue
            except Exception as e:
                print(f"エラー: インプットファイル {file_path} の読み込み中にエラーが発生しました: {e}")
                raise

        # プレースホルダを置き換える
        # プレースホルダはキーに対応する大文字の文字列を想定（例: {PLACEHOLDER}）
        placeholder_tag = '{' + placeholder.upper() + '}'
        
        # 複数のファイル内容を結合して置き換えテキストとする（改行2つで区切る例）
        combined_content = "\n\n".join(replacement_content)

        if combined_content:
             # プロンプトテキスト内のプレースホルダを置き換える
             prompt_text = prompt_text.replace(placeholder_tag, combined_content)
        else:
             # ファイル内容が空の場合、プレースホルダを空文字列で置き換える
             prompt_text = prompt_text.replace(placeholder_tag, "")

    return prompt_text

def call_gemini_api(prompt_text, settings):
    """Gemini APIを呼び出し、結果を受け取る"""
    
    # 3. API処理
    client = genai.Client(api_key=settings['api_key'])
    model = 'gemini-2.5-flash'  # 使用するモデルは適宜変更可能

    response = None
    for attempt in range(settings['try_times']):
        try:
            print(f"API呼び出し試行回数: {attempt + 1}/{settings['try_times']}")
            # APIにプロンプトを投入
            response = client.models.generate_content(
                model=model,
                contents=prompt_text,
            )
            break  # 成功
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

    # 4. 結果の受領と分割
    response_text = response.text
    # デバッグ用: レスポンス確認
    # print(response_text)
    separator = settings['separator']
    
    # セパレータで分割。strip()で前後の空白を除去
    parts = [p.strip() for p in response_text.split(separator) if p.strip()]
    
    return parts

def write_outputs(parts, settings):
    """API応答の配列をファイルとして出力する"""
    
    dist_dir = settings['dist']
    dist_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"結果をディレクトリ {dist_dir.resolve()} に出力します。")

    # ファイル名とファイル内容が交互に並んでいることを期待
    # parts[0] = 1つ目のファイル名, parts[1] = 1つ目のファイル内容, ...
    if len(parts) % 2 != 0:
        print("警告: APIからの応答の要素数が奇数です。最後の要素はファイル名または内容のどちらかとして扱われます。")

    for i in range(0, len(parts), 2):
        file_name = parts[i]
        
        # ファイル名の正規化と絶対パスの禁止
        # パス操作の安全性を高めるため、ファイル名からパス区切り文字を除去するなどの処理を検討すべき
        safe_file_name = file_name.replace('/', '_').replace('\\', '_').replace('..', '')
        
        output_path = dist_dir / safe_file_name
        
        # ファイル内容を取得
        file_content = parts[i+1] if i + 1 < len(parts) else "--- 内容なし ---"

        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(file_content)
            print(f"ファイル出力成功: {output_path.name}")
        except Exception as e:
            print(f"エラー: ファイル {output_path} の書き込み中にエラーが発生しました: {e}")


def main():
    """メイン処理"""
    try:
        # 1. 各種初期情報の読み込み
        settings = load_settings()
        
        # 2. プロンプトファイルの読み込み & 3. インプットファイルの読み込みと置き換え
        final_prompt = read_prompt_and_replace(settings)
        
        # デバッグ用: 最終的なプロンプトの確認
        # print("\n--- 最終的なプロンプト ---")
        # print(final_prompt)
        # print("--------------------------\n")
        
        # 3. API処理 & 4. 結果の受領と分割
        response_parts = call_gemini_api(final_prompt, settings)
        
        # 4. 結果のファイル出力
        write_outputs(response_parts, settings)
        
        print("\n✅ 全ての処理が完了しました。")

    except Exception as e:
        print(f"\n❌ スクリプトの実行中に致命的なエラーが発生しました: {e}")
        # スクリプトをエラー終了させる
        exit(1)

if __name__ == '__main__':
    main()