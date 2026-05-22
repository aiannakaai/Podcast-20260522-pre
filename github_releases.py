import time
import requests
from config import CLAUDE_CODE_REPO


def get_releases(max_per_page: int = 20) -> list[dict]:
    """GitHub Releases API からリリース情報を取得（認証不要）"""
    url = f"https://api.github.com/repos/{CLAUDE_CODE_REPO}/releases"
    headers = {"Accept": "application/vnd.github+json"}

    print(f"GitHub Releases から取得中: {url}")

    for attempt in range(3):
        try:
            resp = requests.get(
                url,
                headers=headers,
                params={"per_page": max_per_page},
                timeout=30,
            )
            resp.raise_for_status()
            releases = resp.json()
            print(f"{len(releases)} 件のリリースを取得しました")
            return releases
        except requests.RequestException as e:
            if attempt < 2:
                print(f"取得エラー ({e})、60秒後にリトライ...")
                time.sleep(60)
            else:
                raise RuntimeError(f"GitHub Releases API の取得に失敗: {e}")
    return []
