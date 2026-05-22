import time
from config import RETRY_WAIT_SECONDS, MAX_RETRIES


def is_retriable_error(e: Exception) -> bool:
    error_str = str(e).lower()
    return any(x in error_str for x in [
        "429", "503", "resource exhausted", "service unavailable",
        "quota exceeded", "rate limit", "too many requests",
    ])


def retry_with_fallback(func, primary: str, fallback: str):
    """プライマリ・フォールバックモデルでリトライ実行"""
    for model in [primary, fallback]:
        for attempt in range(MAX_RETRIES):
            try:
                return func(model)
            except Exception as e:
                if is_retriable_error(e):
                    if attempt < MAX_RETRIES - 1:
                        print(f"  API エラー ({type(e).__name__}: {e})")
                        print(f"  {RETRY_WAIT_SECONDS}秒後にリトライ ({attempt + 1}/{MAX_RETRIES})...")
                        time.sleep(RETRY_WAIT_SECONDS)
                    else:
                        print(f"  [{model}] リトライ上限到達。次のモデルへ移行...")
                        break
                else:
                    raise
    raise RuntimeError("プライマリ・フォールバック両モデルでの処理に失敗しました")
