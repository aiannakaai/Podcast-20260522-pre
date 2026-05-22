import json
import os
import sys
from datetime import datetime, timedelta, timezone

from google import genai

import config
from drive_upload import upload_podcast
from github_releases import get_releases
from research import research_version
from script_gen import generate_script
from tts import generate_audio


def load_researched_versions() -> set:
    path = config.RESEARCHED_VERSIONS_JSON
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return set(json.load(f).get("researched", []))
    return set()


def save_researched_versions(researched: set) -> None:
    data = {
        "researched": sorted(researched),
        "last_updated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    with open(config.RESEARCHED_VERSIONS_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"保存: {config.RESEARCHED_VERSIONS_JSON}")


def save_json(data, path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"保存: {path}")


def get_target_date() -> str:
    date_override = os.environ.get("DATE_OVERRIDE", "").strip()
    if date_override:
        print(f"日付オーバーライド使用: {date_override}")
        return date_override
    jst = timezone(timedelta(hours=9))
    return datetime.now(jst).strftime("%Y-%m-%d")


def main() -> None:
    print("=== Podcast 生成開始 ===")

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("エラー: GEMINI_API_KEY が設定されていません")
        sys.exit(1)

    target_date = get_target_date()
    print(f"対象日付: {target_date}")

    os.makedirs(config.OUTPUT_DIR, exist_ok=True)

    client = genai.Client(api_key=api_key)

    # Step 1: GitHub Releases から最新バージョンを取得
    print("\n[Step 1] GitHub Releases からバージョン取得...")
    releases = get_releases()
    if not releases:
        print("リリースが見つかりません。終了します。")
        sys.exit(0)

    # Step 2: 未調査バージョンを特定
    researched = load_researched_versions()
    print(f"調査済みバージョン: {sorted(researched)}")

    target_release = None
    for release in releases:
        tag = release.get("tag_name", "")
        if (
            tag
            and tag not in researched
            and not release.get("draft", False)
            and not release.get("prerelease", False)
        ):
            target_release = release
            break

    if not target_release:
        print("新しい未調査バージョンはありません。終了します。")
        sys.exit(0)

    version = target_release["tag_name"]
    release_notes = target_release.get("body") or "変更点の詳細は GitHub Releases を参照してください。"
    print(f"対象バージョン: {version}")

    # Step 3: 調査
    print(f"\n[Step 2] {version} の変更点を調査中...")
    research = research_version(client, version, release_notes)
    save_json(research, config.RESEARCH_JSON)

    # Step 4: 台本生成
    print("\n[Step 3] Podcast 台本を生成中...")
    script = generate_script(client, research)
    save_json(script, config.SCRIPT_JSON)

    # Step 5: 音声生成
    print("\n[Step 4] 音声を生成中...")
    mp3_path = generate_audio(client, script)

    # Step 6: Google Drive アップロード
    print("\n[Step 5] Google Drive にアップロード中...")
    link = upload_podcast(mp3_path, version, target_date)

    # Step 7: 調査済みとして記録
    researched.add(version)
    save_researched_versions(researched)

    print(f"\n=== 完了: {version} の Podcast を生成しました ===")
    print(f"Drive リンク: {link}")


if __name__ == "__main__":
    main()
