# Claude Code Podcast Generator

Claude Code の最新バージョンを自動調査し、日本語 Podcast を毎日生成して Google Drive にアップロードするシステムです。

## 概要

- **情報収集**: Gemini + Google Search Grounding で Claude Code の最新リリース情報を調査
- **リリース取得**: GitHub Releases API（認証不要）
- **Podcast 生成**: 田中（男性）と 鈴木（女性）の二人による約 5 分の会話
- **音声合成**: Gemini TTS（MultiSpeakerVoiceConfig）
- **保存先**: Google Drive の `Podcasts/{バージョン}_{日付}/podcast.mp3`
- **定期実行**: GitHub Actions（毎日 JST 6:00）

---

## セットアップ手順

### 1. GEMINI_API_KEY の取得と設定

1. [Google AI Studio](https://aistudio.google.com/apikey) にアクセス
2. 「API キーを作成」からキーを発行
3. GitHub リポジトリの **Settings → Secrets and variables → Actions → New repository secret** を開く
4. Name: `GEMINI_API_KEY`、Value: 取得したキーを入力して保存

---

### 2. GOOGLE_CLIENT_ID の取得と設定

1. [GCP Console](https://console.cloud.google.com/) でプロジェクトを作成（または選択）
2. **API とサービス → OAuth 同意画面** を開き、以下を設定:
   - ユーザータイプ: **外部**
   - アプリ名・連絡先メールを入力
   - スコープに `https://www.googleapis.com/auth/drive.file` を追加
   - **⚠️ 重要: 「アプリを公開」ボタンで本番環境に設定する（テスト環境のまま放置すると refresh token が 7 日で失効）**
3. **API とサービス → 認証情報 → 認証情報を作成 → OAuth クライアント ID** を選択
4. アプリケーションの種類: **ウェブアプリケーション**
5. 承認済みリダイレクト URI に `https://developers.google.com/oauthplayground` を追加して保存
6. 表示されたクライアント ID を GitHub Secret に登録: Name: `GOOGLE_CLIENT_ID`

---

### 3. GOOGLE_CLIENT_SECRET の設定

- 上記手順 2-6 で取得したクライアントシークレットを GitHub Secret に登録
- Name: `GOOGLE_CLIENT_SECRET`

---

### 4. GOOGLE_REFRESH_TOKEN の取得と設定

OAuth2.0 Playground を使って refresh token を取得します。

1. [OAuth2.0 Playground](https://developers.google.com/oauthplayground) にアクセス
2. 右上の歯車アイコン（⚙）をクリックし、以下を設定:
   - 「Use your own OAuth credentials」にチェック
   - OAuth Client ID: 手順 2 で取得したクライアント ID
   - OAuth Client Secret: 手順 3 で取得したシークレット
3. 左ペインの「Step 1: Select & authorize APIs」で以下を入力して「Authorize APIs」:
   ```
   https://www.googleapis.com/auth/drive.file
   ```
4. Google アカウントでログインして権限を付与
5. 「Step 2: Exchange authorization code for tokens」で「Exchange authorization code for tokens」をクリック
6. 表示された `refresh_token` の値をコピー
7. GitHub Secret に登録: Name: `GOOGLE_REFRESH_TOKEN`

---

## GitHub Actions の実行

### 定期実行（自動）

毎日 JST 6:00（UTC 21:00）に自動実行されます。新しい Claude Code バージョンがある場合のみ Podcast を生成します。

### 手動実行

1. GitHub リポジトリの **Actions → Daily Podcast Generation → Run workflow**
2. 必要に応じて「日付オーバーライド」に日付を入力（例: `2026-05-22`）
3. 「Run workflow」をクリック

---

## ファイル構成

```
.
├── .github/workflows/podcast.yml  # GitHub Actions ワークフロー
├── output/
│   ├── research.json              # 調査結果（git に保存）
│   └── script.json                # 台本（git に保存）
├── researched_versions.json       # 調査済みバージョン記録（git に保存）
├── config.py                      # 話者設定・モデル名などの定数
├── main.py                        # メイン処理
├── github_releases.py             # GitHub Releases API クライアント
├── research.py                    # Gemini で調査
├── script_gen.py                  # 台本生成
├── tts.py                         # 音声生成
├── drive_upload.py                # Google Drive アップロード
├── utils.py                       # リトライユーティリティ
└── requirements.txt               # Python 依存ライブラリ
```

## GitHub Secrets 一覧

| Secret 名 | 説明 | 設定順 |
|---|---|---|
| `GEMINI_API_KEY` | Google AI Studio の API キー | 1番目 |
| `GOOGLE_CLIENT_ID` | GCP OAuth クライアント ID | 2番目 |
| `GOOGLE_CLIENT_SECRET` | GCP OAuth クライアントシークレット | 3番目 |
| `GOOGLE_REFRESH_TOKEN` | OAuth2.0 Playground で取得した refresh token | 4番目 |

## 注意事項

- GCP の OAuth 同意画面は必ず**本番環境（公開済み）**に設定してください。テスト環境のままだと refresh token が 7 日で失効します。
- GitHub リポジトリはパブリックに設定することで GitHub Actions の無料枠が無制限になります。
- 音声ファイル（`.wav`、`.mp3`）は `.gitignore` により git に保存されません。JSON のみ保存されます。
