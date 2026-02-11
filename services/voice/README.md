# VOICEVOX Voice Notification Service

ナースロボ＿タイプＴの声でタスクを親しみやすく読み上げるサービスです。

## 概要

このサービスは以下の機能を提供します：

1. **タスク発注時の音声通知**: BrainサービスがタスクをDashboardに登録する際、自動的にVOICEVOXで音声を生成し読み上げます
2. **LLM統合**: タスクデータから自然な日本語文章をLLMで生成
3. **多様性重視**: 同じ内容でも毎回異なる表現を使用（キャッシング無効）
4. **フィードバック機能**: タスク完了時の「ありがとうございます」などの応答も対応

## アーキテクチャ

```
Brain Service → Voice Service → LLM → 自然な文章生成
                ↓
            VOICEVOX Engine → 音声合成(ナースロボ＿タイプＴ)
                ↓
            WAVファイル生成 → 再生
```

## 使用技術

- **VOICEVOX Engine**: CPU版（LLMとのリソース競合を避けるため）
- **Voice Character**: ナースロボ＿タイプＴ (Speaker ID: 47)
- **FastAPI**: Voice Service API
- **LLM**: 自然な日本語文章生成

## ディレクトリ構成

```
services/voice/
├── Dockerfile                  # Voice Service コンテナ
├── requirements.txt
├── voicevox/
│   └── Dockerfile             # VOICEVOX Engine コンテナ
└── src/
    ├── main.py                # FastAPI アプリケーション
    ├── models.py              # データモデル
    ├── voicevox_client.py     # VOICEVOX API クライアント
    └── speech_generator.py    # LLM統合・文章生成
```

## API エンドポイント

### `POST /api/voice/announce`
タスクを音声で読み上げる

**Request:**
```json
{
  "task": {
    "title": "コーヒー豆の補充",
    "description": "給湯室のコーヒー豆がなくなっています",
    "location": "給湯室",
    "bounty_gold": 50,
    "urgency": 2,
    "zone": "2F"
  }
}
```

**Response:**
```json
{
  "audio_url": "/audio/task_12345.wav",
  "text_generated": "お願いがあります。2階給湯室でコーヒー豆の補充をお願いします。50神保ポイントを獲得できます。",
  "duration_seconds": 5.2
}
```

### `POST /api/voice/feedback/{feedback_type}`
フィードバックメッセージを生成

**Feedback Types:**
- `task_completed`: タスク完了時の応答
- `task_accepted`: タスク受諾時の応答

## セットアップ

### 1. Docker Composeで起動

```bash
cd infra
docker-compose up -d voicevox voice-service
```

### 2. サービス確認

```bash
# VOICEVOX Engine
curl http://localhost:50021/version

# Voice Service
curl http://localhost:8002/
```

### 3. テスト実行

```bash
cd /home/sin/code/gemini/bigbrother
python3 test_voice_service.py
```

テストスクリプトは以下を検証します：
- VOICEVOX Engineの動作確認
- Voice Serviceの正常性
- タスク読み上げ機能
- フィードバック生成
- 音声の多様性（毎回異なる表現）

## 使用例

### Brain Serviceからの自動読み上げ

```python
from dashboard_client import DashboardClient

client = DashboardClient(enable_voice=True)

# タスクを作成すると自動的に音声で読み上げられる
await client.create_task(
    title="コーヒー豆の補充",
    description="給湯室のコーヒー豆がなくなっています",
    bounty=50,
    task_types=["supply"],
    urgency=2,
    zone="2F",
    announce=True  # デフォルトでTrue
)
```

### 直接APIを呼び出す

```python
import requests

response = requests.post(
    "http://localhost:8002/api/voice/announce",
    json={
        "task": {
            "title": "掃除機をかける",
            "description": "オフィスの床を掃除してください",
            "location": "オフィス",
            "bounty_gold": 30,
            "urgency": 1,
            "zone": "1F"
        }
    }
)

result = response.json()
print(result["text_generated"])

# 音声ファイルをダウンロード
audio_url = f"http://localhost:8002{result['audio_url']}"
audio = requests.get(audio_url)
with open("task_announcement.wav", "wb") as f:
    f.write(audio.content)

# 再生
# aplay task_announcement.wav
```

## 環境変数

### Voice Service (`voice-service` container)

- `VOICEVOX_URL`: VOICEVOX EngineのURL（デフォルト: `http://voicevox:50021`）
- `LLM_API_URL`: LLM APIのURL（デフォルト: `http://brain:8000/llm`）

### Dashboard Client

- `VOICE_SERVICE_URL`: Voice ServiceのURL（デフォルト: `http://voice-service:8000`）

## 設計方針

### CPU版を使用
LLMとGPUリソースの競合を避けるため、VOICEVOX CPU版を使用しています。

### キャッシング無効
同じ内容のタスクでも毎回異なる表現を生成するため、音声キャッシングは実装していません。

### ストリーミング不要
十分高速なため、リアルタイムストリーミング機能は実装していません。

### 単一ボイス
ナースロボ＿タイプＴ（Speaker ID: 47）のみを使用します。

## トラブルシューティング

### VOICEVOX Engineが起動しない
```bash
# ログを確認
docker logs soms-voicevox

# コンテナを再起動
docker restart soms-voicevox
```

### LLMが応答しない
Voice Serviceはフォールバック機能を持っており、LLMが失敗しても簡易テンプレートで音声を生成します。

### 音声が生成されない
```bash
# Voice Serviceのログを確認
docker logs soms-voice

# VOICEVOX APIを直接テスト
curl -X POST "http://localhost:50021/audio_query?speaker=47&text=テストメッセージです"
```

## 今後の拡張

- 感情表現: 緊急度に応じた抑揚・速度調整
- 多言語対応: 英語など他言語への対応
