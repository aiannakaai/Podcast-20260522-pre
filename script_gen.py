import json
import re

from google import genai
from google.genai import types

from config import (
    RESEARCH_MODEL_PRIMARY,
    RESEARCH_MODEL_FALLBACK,
    SPEAKERS,
    TARGET_DURATION_MINUTES,
    TTS_CHUNK_MAX_CHARS,
)
from utils import retry_with_fallback


def generate_script(client: genai.Client, research: dict) -> list[dict]:
    """調査結果から Podcast 台本を JSON 形式で生成"""
    speaker_1 = SPEAKERS[0]["name"]
    speaker_2 = SPEAKERS[1]["name"]

    prompt = f"""以下の調査内容をもとに、Claude Code {research['version']} についての日本語 Podcast 台本を作成してください。

調査内容:
{research['content'][:4000]}

要件:
- 話者: {speaker_1}（男性・技術解説担当）、{speaker_2}（女性・質問・まとめ担当）
- 目標: 約{TARGET_DURATION_MINUTES}分の会話（合計文字数 1500〜2500 文字程度）
- 出力形式: JSON 配列のみ（前後のテキスト・コードブロックは不要）
- 各要素: {{"speaker": "話者名", "text": "発話内容"}}
- 発話内容にコードや記号（山かっこ、ハッシュ、バッククォートなど）は含めない（音声読み上げのため）
- 自然な会話形式で、聴き手が楽しめる内容に

出力例:
[
  {{"speaker": "{speaker_1}", "text": "こんにちは、今日のポッドキャストへようこそ。"}},
  {{"speaker": "{speaker_2}", "text": "はい、よろしくお願いします。"}}
]

上記の形式の JSON 配列のみを出力してください。"""

    def _call(model: str) -> list[dict]:
        print(f"  [{model}] 台本生成中...")
        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(temperature=0.9),
        )
        text = response.text.strip()

        # コードブロックを除去してから JSON を抽出
        text = re.sub(r"```(?:json)?", "", text).strip()
        json_match = re.search(r"\[[\s\S]*\]", text)
        if json_match:
            text = json_match.group(0)

        script = json.loads(text)

        valid_names = {s["name"] for s in SPEAKERS}
        for turn in script:
            if turn.get("speaker") not in valid_names:
                raise ValueError(f"不正な話者名: {turn.get('speaker')}")

        print(f"  台本生成完了: {len(script)} 発話")
        return script

    return retry_with_fallback(_call, RESEARCH_MODEL_PRIMARY, RESEARCH_MODEL_FALLBACK)


def split_script_into_chunks(script: list[dict], max_chars: int = TTS_CHUNK_MAX_CHARS) -> list[str]:
    """台本を max_chars 未満のチャンクに分割（発話単位で区切る）"""
    chunks = []
    current_lines: list[str] = []
    current_len = 0

    for turn in script:
        line = f"{turn['speaker']}: {turn['text']}"
        line_len = len(line) + 1  # +1 for newline

        if current_lines and current_len + line_len > max_chars:
            chunks.append("\n".join(current_lines))
            current_lines = [line]
            current_len = line_len
        else:
            current_lines.append(line)
            current_len += line_len

    if current_lines:
        chunks.append("\n".join(current_lines))

    return chunks
