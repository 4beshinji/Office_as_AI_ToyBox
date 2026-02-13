# SOMS (Symbiotic Office Management System) — システム全体像

**最終更新**: 2026-02-13
**対象バージョン**: main ブランチ (未コミット変更含む)

---

## 目次

1. [このシステムは何か](#1-このシステムは何か)
2. [設計思想とビジョン](#2-設計思想とビジョン)
3. [4層アーキテクチャ](#3-4層アーキテクチャ)
4. [中央知能: Brain サービス](#4-中央知能-brain-サービス)
5. [知覚層: Perception サービス](#5-知覚層-perception-サービス)
6. [エッジ層: IoT デバイス](#6-エッジ層-iot-デバイス)
7. [人間インターフェース: Dashboard & Voice](#7-人間インターフェース-dashboard--voice)
8. [通信基盤: MCP over MQTT](#8-通信基盤-mcp-over-mqtt)
9. [安全機構](#9-安全機構)
10. [データフロー: エンドツーエンド](#10-データフロー-エンドツーエンド)
11. [技術スタック一覧](#11-技術スタック一覧)
12. [ディレクトリ構成](#12-ディレクトリ構成)
13. [デプロイメントモード](#13-デプロイメントモード)

---

## 1. このシステムは何か

SOMS は **LLM（大規模言語モデル）を「脳」として持つ、自律型オフィス環境管理システム** である。

従来のビル管理システム（BMS）が「室温26度超過→冷房ON」のような **決定論的ルール** で動作するのに対し、SOMS は LLM の推論能力を活用して **文脈を理解した判断** を行う。

### 具体例

| 従来のBMS | SOMS |
|-----------|------|
| CO2が1000ppm超過 → 換気ON | CO2が1000ppmで3人が作業中 → 換気タスク作成 + 音声で「窓を開けましょう」 |
| 温度センサー異常値 → アラーム | 30秒以内に5度変化 → センサー改竄の可能性を検知、ユーモラスに指摘 |
| 人感センサーON → 照明ON | 30分間同じ姿勢 → 健康を気遣い「体を動かしませんか？」と声をかける |
| — (対応不可) | ホワイトボードが汚れている → 清掃タスクを報酬付きで掲示 |

### 核心的な問い

> **スマートホームAPIで操作できない物理的タスクを、AIはどう解決するか？**

SOMS の答え: **人間を「高度な汎用アクチュエータ」として経済的インセンティブで動かす**。

LLM が状況を判断し、必要なタスクを生成し、報酬（最適化承認スコア）を提示して人間に依頼する。人間は自由意志でタスクを受諾・完了し、ダッシュボードでスコアを蓄積する。これが **「共生（Symbiosis）」** の意味である。

---

## 2. 設計思想とビジョン

### 2.1 有機体メタファー

システム全体を一つの **有機体** として設計している:

| 生物学的アナロジー | SOMS コンポーネント |
|-------------------|-------------------|
| 脳 (Brain) | LLM (Qwen2.5 / Mock LLM) |
| 神経系 (Nervous System) | MQTT ブローカー (Mosquitto) |
| 感覚器 (Senses) | センサー (BME680, MH-Z19C) + カメラ (YOLOv11) |
| 手足 (Limbs) | ESP32 エッジデバイス (リレー, LED) |
| 外部協力者 | 人間 (ダッシュボード経由のタスク実行者) |
| 声 (Voice) | VOICEVOX 音声合成 |

### 2.2 六つの設計原則

#### 原則1: 自律性 (Agency) > 自動化 (Automation)

ルールベースの自動化ではなく、LLM の推論による **自律的判断** を重視する。「環境の快適性とエネルギー効率の最大化」という **目的関数** に向けて、状況に応じてツールを選択し行動する。

#### 原則2: 憲法的AI (Constitutional AI)

LLM の行動を **コードのハードコードではなく、言語による行動原則（憲法）** で制約する。システムプロンプトに組み込まれた原則:

- **安全最優先**: 健康・安全に関わる問題は最高優先度
- **コスト意識**: 報酬は難易度に比例 (500〜5000)、むやみに人間に依頼しない
- **重複回避**: タスク作成前に既存タスクを必ず確認
- **正常時は何もしない**: 全指標が正常なら介入しない
- **プライバシー**: 個人を特定する情報は扱わない

#### 原則3: イベント駆動 (Event-Driven Architecture)

Node-RED や LangChain のような重量級ミドルウェアを排し、**Python + MQTT による純粋なイベント駆動** を採用。理由:

- **低レイテンシ**: MQTT pub/sub はミリ秒単位
- **疎結合**: 各コンポーネントは共通トピックのみで連携
- **LLM 親和性**: Python コードはテキストベースのため LLM が理解可能

#### 原則4: コードファースト (Code-First)

ビジュアルプログラミングを排除し、全ロジックを Python/C++ コードで記述。LLM がシステムの論理構造を直接理解・修正可能な **透明性** を確保する。

#### 原則5: 善意モデル (Good Faith / Honor System)

経済システムは **ユーザー認証なし・性善説ベース**:

- ログイン不要: 誰でもタスクを受諾可能
- 報酬はシグナル: 「緊急度」と「感謝」を伝える手段であり、リソースのゲートキーピングではない
- 不正対策は最小限: 物理的に状態が変わらなければタスクを再発行するだけ

#### 原則6: ローカルファースト (Local-First)

全処理をオンプレミスで完結。映像・音声・センサーデータは一切クラウドに送信しない。32GB VRAM の GPU サーバー1台で LLM 推論からコンピュータビジョンまで賄う。

### 2.3 名前の由来: "Office as AI ToyBox"

リポジトリ名 `Office_as_AI_ToyBox` は、オフィス空間を AI の「おもちゃ箱」に見立てる発想を反映している。センサー、カメラ、マイコン、LLM、音声合成といった技術を自由に組み合わせ、**AI が物理世界と対話する実験場** としてのオフィスを構築する。

---

## 3. 4層アーキテクチャ

```
┌────────────────────────────────────────────────────────────┐
│                    人間インターフェース層                      │
│  Dashboard (React 19)  |  Voice (VOICEVOX)  |  タスク経済    │
├────────────────────────────────────────────────────────────┤
│                       中央知能層                             │
│  Brain: ReAct認知ループ | WorldModel | ToolExecutor | 安全弁  │
├────────────────────────────────────────────────────────────┤
│                       知覚層                                │
│  YOLOv11 (物体検出/姿勢推定) | カメラ自動検出 | 活動分析      │
├────────────────────────────────────────────────────────────┤
│                       エッジ層                              │
│  ESP32 (MicroPython/C++) | センサー | リレー | MQTT通信       │
└────────────────────────────────────────────────────────────┘
         ↕ 全層が MQTT (Mosquitto) で接続 ↕
```

---

## 4. 中央知能: Brain サービス

**場所**: `services/brain/src/`

Brain は SOMS の中核であり、**ReAct (Think → Act → Observe) 認知ループ** で動作する。

### 4.1 ReAct 認知ループ

```
[トリガー] ← MQTT イベント (3秒バッチ) or 30秒定期
    │
    ▼
[1. THINK] WorldModel から現在のオフィス状態を取得
    │       → LLM に状態 + 行動原則を送信
    ▼
[2. ACT]   LLM が判断 → ツール呼び出し (0〜複数)
    │       → ToolExecutor が安全検証 → 実行
    ▼
[3. OBSERVE] ツール結果を LLM にフィードバック
    │         → LLM が追加行動を判断 (最大5反復)
    ▼
[完了] LLM が「これ以上の行動は不要」と判断 → ループ終了
```

**制約パラメータ**:
- 最大反復回数: 5回/サイクル (暴走防止)
- サイクル間隔: 30秒 (定期), 3秒 (イベント駆動時のバッチ遅延)
- LLM タイムアウト: 120秒
- MCP デバイス応答: 10秒

### 4.2 WorldModel: AI の「世界認識」

WorldModel はセンサーデータを統合し、LLM に構造化された「世界の状態」を提供する。

**データ構造**:
```
WorldModel
├── zones: Dict[zone_id] → ZoneState
│   ├── environment: { temperature, humidity, co2, illuminance }
│   ├── occupancy: { person_count, activity_class, posture_status }
│   ├── devices: Dict[device_id] → { power_state, specific_state }
│   └── events: List[Event] (直近50件)
└── sensor_fusion: 重み付き平均 (鮮度×信頼度)
```

**センサーフュージョン**: 複数センサーの読み取り値を指数減衰加重平均で統合。新しい値ほど重みが大きい:
- 温度: 半減期120秒 (緩やかな変化)
- CO2: 半減期60秒 (在室に敏感)
- 在室: 半減期30秒 (リアルタイム性重視)

**イベント検知**: 状態変化を検出し、クールダウン付きで発火:

| イベント | 条件 | クールダウン |
|---------|------|------------|
| CO2閾値超過 | >1000ppm | 10分 |
| 温度急変 | 3度以上/短時間 | — |
| 長時間座位 | 同姿勢30分以上 | 1時間 |
| センサー改竄 | 急激な値変動 | 5分 |

### 4.3 LLM ツール (5種)

Brain が LLM に提供するツール:

| ツール | 用途 | 副作用 |
|-------|------|--------|
| `create_task` | 人間向けタスクをダッシュボードに掲示 | タスク作成 + 音声合成 |
| `send_device_command` | エッジデバイスを MCP 経由で制御 | 物理デバイス操作 |
| `speak` | 音声のみのアナウンス (タスクなし) | 音声再生 |
| `get_zone_status` | ゾーンの詳細状態を取得 | なし (読み取り専用) |
| `get_active_tasks` | 既存タスク一覧 (重複防止) | なし (読み取り専用) |

**ツール選択の指針** (システムプロンプトに記述):

- 「30分座りっぱなし → 運動促進」 → `speak` (助言であり、タスクではない)
- 「CO2 1000ppm超 + 人がいる」 → `create_task` (物理的行動が必要)
- 「センサー値の急変」 → `speak` (ユーモラスなトーンで指摘)
- 「全指標正常」 → **何もしない**

### 4.4 タスクスケジューリング

タスクは即時配信されるとは限らない。文脈を考慮したスマートディスパッチ:

| 条件 | 判定 |
|------|------|
| 緊急度4 (CRITICAL) | 即時配信 |
| 緊急度3 + 在室者あり | 即時配信 |
| ゾーンに誰もいない | キューイング (人が来るまで待機) |
| 深夜 (22時以降) + 低緊急度 | キューイング (翌朝まで) |
| 24時間経過 | 強制配信 |

---

## 5. 知覚層: Perception サービス

**場所**: `services/perception/src/`

YOLOv11 ベースのコンピュータビジョンシステム。「ピクセル → 意味」の変換を担う。

### 5.1 プラガブル・モニター設計

モニターは YAML 設定 (`config/monitors.yaml`) で宣言的に定義:

| モニター | 頻度 | 解像度 | 目的 |
|---------|------|--------|------|
| OccupancyMonitor | 5秒 | QVGA | 在室人数の高速検知 |
| ActivityMonitor | 3秒 | VGA | 活動レベル + 姿勢分析 (2段階推論) |
| WhiteboardMonitor | 60秒 | VGA | ホワイトボード汚れ検知 (Canny エッジ) |

### 5.2 活動分析: 4層バッファ

長時間の姿勢追跡のため、時間解像度を段階的に粗くする:

| 層 | 保持期間 | 解像度 | 用途 |
|----|---------|--------|------|
| Tier 0 (raw) | 60秒 | 毎フレーム | 短期活動レベル |
| Tier 1 | 10分 | 10秒ごと | 中期活動傾向 |
| Tier 2 | 1時間 | 1分ごと | 長期姿勢追跡 |
| Tier 3 | 4時間 | 5分ごと | 長時間座位検知 |

**姿勢正規化**: 位置・スケール不変の骨格特徴量で比較 (アンカー: 腰中点, スケール: 肩幅)

### 5.3 カメラ自動検出

3段階パイプライン:
1. **ポートスキャン**: ネットワーク上のカメラポート (80, 81, 554, 8554) を非同期TCP接続
2. **URL プローブ**: 候補URLパターンで OpenCV 接続テスト
3. **YOLO 検証**: フレーム取得 → 物体検出で「実カメラ」確認

---

## 6. エッジ層: IoT デバイス

**場所**: `edge/`

### 6.1 デバイス種類

| デバイス | ハードウェア | ファームウェア | センサー |
|---------|------------|--------------|---------|
| sensor-02 | Seeed XIAO ESP32-C6 | MicroPython | BME680 (温湿度/気圧/ガス) + MH-Z19C (CO2) |
| sensor-node | ESP32 | MicroPython | DHT22 (温湿度) |
| sensor-node (C++) | ESP32 | PlatformIO C++ | BME680 |
| camera-node | Freenove ESP32 WROVER | PlatformIO C++ | OV2640 カメラ |

### 6.2 共通ライブラリ: `edge/lib/soms_mcp.py`

全 MicroPython デバイスが共有する統一インターフェース:

- **WiFi + MQTT 接続管理** (自動再接続)
- **`config.json` からの設定読み込み** (device_id, zone, broker)
- **Per-channel テレメトリ**: `office/{zone}/sensor/{device_id}/{channel}` → `{"value": X}`
- **MCP ツール登録**: `register_tool(name, callback)` → JSON-RPC 2.0 で呼び出し可能
- **ハートビート**: 60秒間隔で `{topic_prefix}/heartbeat` にステータス送信

### 6.3 診断ツール

`edge/tools/` に17本のスクリプト。I2C スキャン、UART テスト、LED点滅、ハードウェア検証など。ESP32 の REPL で直接実行する開発支援ツール群。

---

## 7. 人間インターフェース: Dashboard & Voice

### 7.1 Dashboard Frontend

**場所**: `services/dashboard/frontend/`
**技術**: React 19 + TypeScript + Vite 7 + Tailwind CSS 4 + Framer Motion

**UI 設計思想: ゲーミフィケーション**

ダッシュボードはタスクを「クエスト」のように提示する:

- **タスクカード**: タイトル、場所、説明、報酬バッジ（金色）、緊急度バッジ（色分け）
- **報酬表示**: 「N 最適化承認スコア」— 意図的に SF 的な名称で、ゲーム的な蓄積感を演出
- **アクション**: 受諾 / 完了 / 無視 の3ボタン
- **動機付けメッセージ**: 「各タスクを遂行し最適化承認スコアを蓄積することで、次世代のシステムへの適合性を証明しましょう。」
- **アニメーション**: Framer Motion によるカード出現・ホバー・ボタンフィードバック

**ポーリング設計**:
- タスク一覧: 5秒間隔で `GET /tasks/`
- 音声イベント: 3秒間隔で `GET /voice-events/recent`
- 完了タスク: 5分後に自動フェードアウト

### 7.2 Dashboard Backend

**場所**: `services/dashboard/backend/`
**技術**: FastAPI + SQLAlchemy (async) + SQLite

**データモデル**:

| モデル | 主要フィールド | 用途 |
|-------|--------------|------|
| Task | title, description, bounty_gold, urgency(0-4), zone, announcement_audio_url, completion_audio_url | タスク管理 |
| VoiceEvent | message, audio_url, tone, zone | 音声イベント記録 |
| User | username, credits | ユーザー (スタブ) |

**主要 API**:
- `GET /tasks/` — アクティブタスク一覧
- `POST /tasks/` — タスク作成 (重複検知付き)
- `PUT /tasks/{id}/complete` — タスク完了
- `GET /voice-events/recent` — 直近60秒の音声イベント
- `GET /tasks/stats` — キュー/アクティブ/完了統計

### 7.3 Voice サービス

**場所**: `services/voice/src/`
**技術**: FastAPI + VOICEVOX (Speaker ID 47: ナースロボ_タイプT)

**音声生成フロー**:
```
テキスト → VOICEVOX /audio_query (韻律生成)
        → VOICEVOX /synthesis (波形生成, WAV 24kHz)
        → pydub (WAV → MP3 変換)
        → /audio/{filename} で配信
```

**音声の使い分け**:

| 場面 | トーン | 例 |
|------|-------|-----|
| 健康助言 | caring | 「少し体を動かしてみませんか？」 |
| 環境警告 | alert | 「CO2濃度が上がっています」 |
| 軽い指摘 | humorous | 「おやおや、センサーに何か起きたかな？」 |
| 一般報告 | neutral | 「環境は快適です」 |

**70文字制限**: `speak` ツールのメッセージは70文字以内。自然な発話ペースを保つための制約。

---

## 8. 通信基盤: MCP over MQTT

### 8.1 なぜ MCP over MQTT か

**MCP (Model Context Protocol)**: AI モデルとツール間の標準インターフェース。通常は HTTP/stdio 上で動作するが、IoT 環境では MQTT が最適:

- **非同期性**: LLM の推論 (秒) とデバイス応答 (ミリ秒〜分) の時間差をブローカーが吸収
- **軽量性**: ESP32 のような低リソースデバイスでも実装可能
- **耐障害性**: QoS による再送制御、LWT によるデバイス生死監視

### 8.2 トピック設計

```
# テレメトリ (Edge → Brain)
office/{zone}/sensor/{device_id}/{channel}  → {"value": X}

# 知覚 (Perception → Brain)
office/{zone}/occupancy                     → {"count": N, "occupied": bool}
office/{zone}/activity                      → {"activity_class": "...", "posture_status": "..."}

# MCP 制御 (Brain → Edge)
mcp/{device_id}/request/call_tool           → JSON-RPC 2.0 リクエスト
mcp/{device_id}/response/{request_id}       → JSON-RPC 2.0 レスポンス

# ハートビート (Edge → Brain)
office/{zone}/sensor/{device_id}/heartbeat  → {"status": "online", "uptime": N}
```

### 8.3 JSON-RPC 2.0 リクエスト/レスポンス

```json
// リクエスト (Brain → Edge)
// Topic: mcp/sensor_01/request/call_tool
{
  "jsonrpc": "2.0",
  "method": "call_tool",
  "params": { "name": "get_status", "arguments": {} },
  "id": "req-uuid-12345"
}

// レスポンス (Edge → Brain)
// Topic: mcp/sensor_01/response/req-uuid-12345
{
  "jsonrpc": "2.0",
  "result": { "temperature": 23.5, "humidity": 45.2 },
  "id": "req-uuid-12345"
}
```

---

## 9. 安全機構

### 9.1 多層防御

```
LLM の出力
  │
  ▼
[憲法的AI] システムプロンプトの行動原則で暴走を抑制
  │
  ▼
[Sanitizer] パラメータの安全性を検証
  │  ├─ 温度範囲: 18〜28度
  │  ├─ ポンプ動作: 最大60秒
  │  ├─ 報酬上限: 5000
  │  ├─ 緊急度範囲: 0〜4
  │  └─ タスク作成: 10件/時間
  │
  ▼
[タイムアウト] LLM: 120秒, MCP: 10秒, 反復: 最大5回
  │
  ▼
[物理デバイス]
```

### 9.2 プライバシー

- **全処理ローカル**: 映像はクラウドに送信しない
- **即時廃棄**: カメラ映像は RAM 上で処理し、保存しない (検出結果の JSON のみ)
- **個人非特定**: システムプロンプトで個人特定情報の扱いを禁止

### 9.3 LLM ハルシネーション対策

- **スキーマ検証**: 存在しないデバイスIDへの命令を拒否
- **範囲チェック**: 物理的に危険なパラメータを拒否
- **レート制限**: タスクの大量生成を防止
- **視覚的グラウンディング**: センサーとカメラの実測値に基づく判断を強制

---

## 10. データフロー: エンドツーエンド

### シナリオ: キッチンの CO2 上昇

```
[T+0s]  ESP32 sensor-02: CO2 = 1050ppm を検知
        → MQTT publish: office/kitchen/sensor/co2_01/co2 → {"value": 1050}

[T+0s]  Brain WorldModel: CO2 値更新、co2_threshold_exceeded イベント発火
        → 認知サイクルをトリガー

[T+3s]  Brain: イベントバッチ遅延完了、ReAct サイクル開始
        → WorldModel の状態を LLM に送信:
          "kitchen: CO2 1050ppm, 3人在室, activity: moderate"

[T+4s]  LLM (Think): "CO2が高い。在室者がいるので換気が必要"
        LLM (Act): get_active_tasks() → 既存の換気タスクなし
                   create_task(title="キッチンの換気", bounty=1500, urgency=3)

[T+5s]  Sanitizer: bounty=1500 ≤ 5000 ✓, urgency=3 ∈ [0,4] ✓
        → DashboardClient: POST /tasks/ → タスク作成
        → Voice Service: VOICEVOX で「キッチンの換気をお願いします」を合成
        → announcement_audio_url をタスクに紐付け

[T+5s]  LLM (Observe): "タスク作成成功"
        LLM: 追加行動不要 → ループ終了

[T+10s] Frontend: 5秒ポーリングで新タスク検出
        → タスクカード表示 + 音声自動再生

[T+??]  人間: 「完了」ボタンを押す
        → completion_audio_url 再生: 「ありがとうございます！」
        → PUT /tasks/{id}/complete
```

---

## 11. 技術スタック一覧

| 層 | 技術 | 用途 |
|----|------|------|
| **LLM** | Qwen2.5 (Ollama, ROCm) / Mock LLM | 推論エンジン |
| **Vision** | YOLOv11 (yolo11s.pt, yolo11s-pose.pt) | 物体検出/姿勢推定 |
| **Backend** | Python 3.11, FastAPI, SQLAlchemy async | API/DB |
| **Frontend** | React 19, TypeScript, Vite 7, Tailwind CSS 4 | UI |
| **Voice** | VOICEVOX, pydub | 日本語音声合成 |
| **Messaging** | MQTT (Mosquitto), paho-mqtt 2.x | イベント通信 |
| **Edge (Python)** | MicroPython, ESP32 | IoT ファームウェア |
| **Edge (C++)** | PlatformIO, ArduinoJson | IoT ファームウェア |
| **Database** | SQLite (aiosqlite) | タスク/イベント永続化 |
| **Container** | Docker Compose v3.8 | デプロイメント |
| **GPU** | AMD ROCm (RDNA 2/3) | LLM/Vision 推論 |

---

## 12. ディレクトリ構成

```
Office_as_AI_ToyBox/
├── services/
│   ├── brain/src/              # 中央知能 (ReAct ループ)
│   │   ├── main.py             #   認知サイクルオーケストレーション
│   │   ├── llm_client.py       #   OpenAI互換 LLM クライアント
│   │   ├── world_model/        #   センサー統合・状態管理
│   │   ├── task_scheduling/    #   文脈対応タスクディスパッチ
│   │   ├── tool_registry.py    #   LLM ツール定義 (5種)
│   │   ├── tool_executor.py    #   ツール実行ルーティング
│   │   ├── system_prompt.py    #   憲法的AI プロンプト
│   │   ├── mcp_bridge.py       #   MQTT ↔ JSON-RPC 2.0 変換
│   │   ├── sanitizer.py        #   入力検証・安全弁
│   │   ├── dashboard_client.py #   REST API クライアント
│   │   └── task_reminder.py    #   定期リマインダー (1時間)
│   ├── perception/src/         # コンピュータビジョン
│   │   ├── main.py             #   モニター管理・起動
│   │   ├── yolo_inference.py   #   YOLOv11 推論ラッパー
│   │   ├── pose_estimator.py   #   骨格推定 (17キーポイント)
│   │   ├── activity_analyzer.py#   4層バッファ活動分析
│   │   ├── camera_discovery.py #   ネットワークカメラ自動検出
│   │   └── monitors/           #   OccupancyMonitor 等
│   ├── dashboard/
│   │   ├── backend/            #   FastAPI + SQLAlchemy
│   │   └── frontend/src/       #   React 19 + Tailwind
│   └── voice/src/              # VOICEVOX 連携
├── edge/
│   ├── lib/soms_mcp.py         # 共通 MCP ライブラリ
│   ├── office/                 # MicroPython ファームウェア
│   │   ├── sensor-02/          #   BME680 + MH-Z19C
│   │   └── sensor-node/        #   DHT22
│   ├── test-edge/              # PlatformIO C++
│   │   ├── sensor-node/        #   BME680 (C++)
│   │   └── camera-node/        #   OV2640 カメラ
│   └── tools/                  # 診断スクリプト (17本)
├── infra/
│   ├── docker-compose.yml      # メイン Docker 構成
│   ├── docker-compose.edge-mock.yml  # 仮想デバイス構成
│   ├── mock_llm/               # キーワードベース LLM シミュレータ
│   ├── virtual_edge/           # 仮想 ESP32 エミュレータ
│   ├── virtual_camera/         # RTSP テストパターン生成
│   ├── mosquitto/              # MQTT ブローカー設定
│   └── scripts/                # セットアップ・テストスクリプト
├── docs/architecture/          # 設計ドキュメント
├── CLAUDE.md                   # 開発者ガイド
├── HANDOFF.md                  # 作業引き継ぎ
└── .env                        # 環境設定
```

---

## 13. デプロイメントモード

### モード1: フルシミュレーション (GPU/ハードウェア不要)

```bash
cd infra
docker compose --env-file ../.env \
  -f docker-compose.yml -f docker-compose.edge-mock.yml \
  up --build -d \
  mosquitto backend frontend brain voice-service voicevox mock-llm virtual-edge
```

- **Mock LLM**: キーワードマッチで tool call を生成 (「温度」+「高」→ create_task)
- **Virtual Edge**: 仮想センサー (温度/CO2/湿度をランダムウォーク)
- **Virtual Camera**: RTSP テストパターン

### モード2: プロダクション (AMD ROCm GPU + 実ハードウェア)

```bash
docker compose -f infra/docker-compose.yml up -d --build
```

- **Ollama + Qwen2.5**: 本物の LLM 推論 (32GB VRAM)
- **Perception**: YOLOv11 による実カメラ映像分析
- **実 ESP32**: BME680/MH-Z19C/OV2640 の実センサーデータ

### サービスポート

| サービス | ポート | コンテナ名 |
|---------|--------|-----------|
| Dashboard Frontend | 80 | soms-frontend |
| Dashboard Backend API | 8000 | soms-backend |
| Mock LLM | 8001 | soms-mock-llm |
| Voice Service | 8002 | soms-voice |
| VOICEVOX Engine | 50021 | soms-voicevox |
| Ollama (LLM) | 11434 | soms-ollama |
| MQTT Broker | 1883 | soms-mqtt |

---

## 補遺: 設計文書索引

| ファイル | 内容 |
|---------|------|
| `docs/architecture/kick-off.md` | 初期構想・技術研究報告書 (包括的) |
| `docs/architecture/detailed_design/01_central_intelligence.md` | LLM + 推論エンジン詳細 |
| `docs/architecture/detailed_design/02_communication_protocol.md` | MCP over MQTT 設計 |
| `docs/architecture/detailed_design/03_perception_verification.md` | 視覚検証システム |
| `docs/architecture/detailed_design/04_economy_dashboard.md` | 経済モデル + ダッシュボード |
| `docs/architecture/detailed_design/05_edge_engineering.md` | エッジデバイス実装 |
| `docs/architecture/detailed_design/06_security_privacy.md` | セキュリティ・プライバシー |
| `docs/architecture/detailed_design/07_container_architecture.md` | コンテナ構成 |
| `CLAUDE.md` | 開発者向けクイックリファレンス |
| `HANDOFF.md` | 直近の作業引き継ぎ |
