CLAUDE_CODE_REPO = "anthropics/claude-code"

SPEAKERS = [
    {"name": "田中", "gender": "male", "voice": "Charon"},
    {"name": "鈴木", "gender": "female", "voice": "Aoede"},
]

DRIVE_FOLDER_NAME = "Podcasts"
TARGET_DURATION_MINUTES = 5

RESEARCH_MODEL_PRIMARY = "gemini-3.5-flash"
RESEARCH_MODEL_FALLBACK = "gemini-2.5-flash"
TTS_MODEL_PRIMARY = "gemini-2.5-pro-preview-tts"
TTS_MODEL_FALLBACK = "gemini-2.5-flash-preview-tts"

TTS_CHUNK_MAX_CHARS = 1799

RETRY_WAIT_SECONDS = 60
MAX_RETRIES = 3

OUTPUT_DIR = "output"
RESEARCH_JSON = "output/research.json"
SCRIPT_JSON = "output/script.json"
RESEARCHED_VERSIONS_JSON = "researched_versions.json"

OAUTH_SCOPE = "https://www.googleapis.com/auth/drive.file"
