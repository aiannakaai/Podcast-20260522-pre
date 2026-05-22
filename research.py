from google import genai
from google.genai import types

from config import RESEARCH_MODEL_PRIMARY, RESEARCH_MODEL_FALLBACK
from utils import retry_with_fallback


def research_version(client: genai.Client, version: str, release_notes: str) -> dict:
    """指定バージョンの変更点を Gemini + Google Search Grounding で調査"""
    prompt = f"""Claude Code {version} の変更点について、日本語で詳しく調査してください。

リリースノート:
{release_notes[:3000]}

以下の観点で詳しく調査し、Podcast のネタとして使える情報を収集してください:
1. 主な新機能と改善点（具体的な使い方も含む）
2. バグ修正（ユーザーへの影響が大きいもの）
3. 開発者コミュニティの反応（GitHub、技術ブログ、SNS など）
4. 実際の活用事例や便利な使い方
5. 今後への期待や注目点

情報はできるだけ具体的に、Podcast で話しやすい形でまとめてください。"""

    def _call(model: str) -> dict:
        print(f"  [{model}] 調査中...")
        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(
                tools=[types.Tool(google_search=types.GoogleSearch())],
                temperature=1.0,
            ),
        )
        return {
            "version": version,
            "content": response.text,
            "model_used": model,
        }

    return retry_with_fallback(_call, RESEARCH_MODEL_PRIMARY, RESEARCH_MODEL_FALLBACK)
