import base64
import os
import time
import wave

from google import genai
from google.genai import types
from pydub import AudioSegment

from config import (
    MAX_RETRIES,
    OUTPUT_DIR,
    RETRY_WAIT_SECONDS,
    SPEAKERS,
    TTS_MODEL_FALLBACK,
    TTS_MODEL_PRIMARY,
)
from script_gen import split_script_into_chunks
from utils import is_retriable_error


def generate_audio(client: genai.Client, script: list[dict]) -> str:
    """台本から音声を生成して MP3 ファイルとして保存"""
    chunks = split_script_into_chunks(script)
    print(f"台本を {len(chunks)} チャンクに分割しました")

    wav_files = []
    for i, chunk_text in enumerate(chunks):
        print(f"チャンク {i + 1}/{len(chunks)} を音声生成中 ({len(chunk_text)} 文字)...")
        wav_path = os.path.join(OUTPUT_DIR, f"chunk_{i}.wav")
        _generate_chunk(client, chunk_text, wav_path)
        wav_files.append(wav_path)
        print(f"  保存: {wav_path}")

    mp3_path = os.path.join(OUTPUT_DIR, "podcast.mp3")
    print("音声チャンクを結合して MP3 に変換中...")
    _merge_to_mp3(wav_files, mp3_path)
    print(f"MP3 保存完了: {mp3_path}")
    return mp3_path


def _build_speech_config() -> types.SpeechConfig:
    speaker_configs = [
        types.SpeakerVoiceConfig(
            speaker=s["name"],
            voice_config=types.VoiceConfig(
                prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=s["voice"])
            ),
        )
        for s in SPEAKERS
    ]
    return types.SpeechConfig(
        multi_speaker_voice_config=types.MultiSpeakerVoiceConfig(
            speaker_voice_configs=speaker_configs
        )
    )


def _generate_chunk(client: genai.Client, text: str, output_path: str) -> None:
    """1 チャンクの音声を生成して WAV ファイルに保存"""
    speech_config = _build_speech_config()

    for model in [TTS_MODEL_PRIMARY, TTS_MODEL_FALLBACK]:
        for attempt in range(MAX_RETRIES):
            try:
                print(f"    [{model}] TTS 生成中...")
                response = client.models.generate_content(
                    model=model,
                    contents=text,
                    config=types.GenerateContentConfig(
                        response_modalities=["AUDIO"],
                        speech_config=speech_config,
                    ),
                )

                pcm_chunks = []
                sample_rate = 24000

                for part in response.candidates[0].content.parts:
                    if not (hasattr(part, "inline_data") and part.inline_data):
                        continue
                    data = part.inline_data.data
                    if isinstance(data, str):
                        data = base64.b64decode(data)
                    pcm_chunks.append(data)

                    mime = part.inline_data.mime_type or ""
                    if "rate=" in mime:
                        try:
                            sample_rate = int(
                                mime.split("rate=")[1].split(";")[0].split(",")[0]
                            )
                        except (ValueError, IndexError):
                            pass

                if not pcm_chunks:
                    raise RuntimeError("TTS レスポンスに音声データがありません")

                _save_pcm_as_wav(b"".join(pcm_chunks), output_path, sample_rate)
                return

            except Exception as e:
                if is_retriable_error(e):
                    if attempt < MAX_RETRIES - 1:
                        print(f"    API エラー ({e})、{RETRY_WAIT_SECONDS}秒後にリトライ ({attempt + 1}/{MAX_RETRIES})...")
                        time.sleep(RETRY_WAIT_SECONDS)
                    else:
                        print(f"    [{model}] リトライ上限到達。次のモデルへ移行...")
                        break
                else:
                    raise

    raise RuntimeError(f"TTS 生成失敗: {output_path}")


def _save_pcm_as_wav(pcm_data: bytes, path: str, sample_rate: int = 24000) -> None:
    with wave.open(path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm_data)


def _merge_to_mp3(wav_files: list[str], output_path: str) -> None:
    if not wav_files:
        raise RuntimeError("結合する WAV ファイルがありません")

    combined = AudioSegment.from_wav(wav_files[0])
    for wav_file in wav_files[1:]:
        combined += AudioSegment.from_wav(wav_file)

    combined.export(output_path, format="mp3", bitrate="128k")
