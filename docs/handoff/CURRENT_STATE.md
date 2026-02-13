# SOMS 作業状態ドキュメント — マルチワーカー引き継ぎ用

**更新日時**: 2026-02-13
**ブランチ**: main
**HEAD**: `0821921` (fix: dashboard migrate function sync and App.tsx useRef for initialLoadDone)
**未コミット**: `docs/architecture/kick-off.md` のみ (590行追加の大幅改訂)

---

## 1. 直近セッション (Session G) の作業内容

### 実施した2つのフェーズ

#### フェーズ1: Brain ロジック7層改善 (全完了・コミット済み)

| Layer | 内容 | 主要コミット |
|-------|------|-------------|
| L1: スレッド安全性 | paho-mqtt thread → asyncio への `call_soon_threadsafe` ディスパッチ | `091f360` |
| L2: 共有HTTPセッション | `aiohttp.ClientSession` を Brain.run() で一元管理、全コンポーネントに注入 | `091f360` |
| L3: ReActループガード | 重複ツール呼出検出、speak上限 (1回/cycle)、連続エラー中断 | `091f360` |
| L4: サイクルレート制限 | `MIN_CYCLE_INTERVAL=25s` でサイクル間隔崩壊を防止 | `091f360` |
| L5: アクション履歴 | 直近30分のツール実行履歴をLLMコンテキストに注入 (speak重複防止) | `091f360` |
| L6: Sanitizer強化 | ゾーン別speakクールダウン (5分)、デバイス許可リスト | `091f360` |
| L7: 死コード除去 | hydro/aqua MQTT購読削除、湿度閾値60%統一 | `091f360` |

#### フェーズ2: ISSUES.md 残存問題の対応

| Issue ID | 内容 | 状態 | コミット |
|----------|------|------|---------|
| M-4 | Voice Service LLM呼出にタイムアウト(30s)追加 | 完了 | `246ffc6` |
| M-6 | Voice requirements.txt をpydantic/aiohttp他サービスと統一 | 完了 | `246ffc6` |
| M-8 | 未使用 `soms_db_data` ボリューム削除 | 完了 | `5abaa10` |
| M-9 | Wallet ポート公開 (8003:8000) 削除 | 完了 | `5abaa10` |
| M-10 | frontend `.dockerignore` 新規作成 | 完了 | `5abaa10` |
| M-11 | edge-mock compose にネットワーク定義追加 | 完了 | `5abaa10` |

---

## 2. ISSUES.md 全32件の解決状態

### 解決済み (25件 / 78%)

| 重要度 | 解決済みID |
|--------|-----------|
| CRITICAL | C-1, C-2, C-3, C-4 (全4件) |
| HIGH | H-1, H-2, H-3, H-4, H-7, H-8 (6/8件) |
| MEDIUM | M-1, M-2, M-3, M-4, M-6, M-8, M-9, M-10, M-11, M-12 (10/12件) |

### 未解決 (7件)

| ID | 重要度 | 内容 | 場所 | 備考 |
|----|--------|------|------|------|
| **H-5** | HIGH | Sanitizer のレート制限タイミング不正 — バリデーション失敗タスクもカウントされる | `services/brain/src/sanitizer.py:56-65` | `record_task_created()` を成功後に移動すべき |
| **H-6** | HIGH (部分) | WalletBadge.tsx レンダーフェーズでの setState | `services/dashboard/frontend/src/components/WalletBadge.tsx:14-16` | React 18+ では動作するが非推奨パターン |
| **M-5** | MEDIUM | Perception の `network_mode: host` と `networks:` の競合 | `infra/docker-compose.yml:168` | host モードでは networks は無視される。定義を削除すべき |
| **M-7** | MEDIUM | Voice Service の Task モデルが簡素すぎる | `services/voice/src/models.py:4-11` | Dashboard の Task スキーマとの乖離 |
| **L-1〜L-8** | LOW | 8件未対応 | 各所 | Dockerfile タグ固定、不要パッケージ、ヘルスチェック等 |

---

## 3. ファイル変更マップ (Session G)

### Brain サービス (`services/brain/src/`)

| ファイル | 変更内容 |
|---------|---------|
| `main.py` | L1-L5, L7: スレッド安全、共有セッション、ReActガード、レート制限、アクション履歴、hydro/aqua削除 |
| `llm_client.py` | L2: session注入 (コンストラクタに `session` パラメータ追加) |
| `dashboard_client.py` | L2: session注入 + `_get_session()` フォールバック (テストスクリプト互換) |
| `tool_executor.py` | L2: session注入 (`_handle_speak` のephemeral session除去) |
| `task_reminder.py` | L2: session注入 (3メソッドのephemeral session除去) |
| `sanitizer.py` | L6: speak_history dict追加、ゾーン別クールダウン、デバイス許可リスト |
| `world_model/world_model.py` | L7: 湿度アラート閾値 70% → 60% |

### Voice サービス (`services/voice/`)

| ファイル | 変更内容 |
|---------|---------|
| `src/speech_generator.py` | M-4: `_call_llm()` に `aiohttp.ClientTimeout(total=30)` 追加 |
| `requirements.txt` | M-6: pydantic 2.10.0→2.5.2, aiohttp 3.11.0→3.9.1, fastapi/uvicorn も統一 |

### インフラ (`infra/`)

| ファイル | 変更内容 |
|---------|---------|
| `docker-compose.yml` | M-8: soms_db_data削除, M-9: wallet ports削除 |
| `docker-compose.edge-mock.yml` | M-11: networks定義追加 (external: infra_soms-net) |

### フロントエンド

| ファイル | 変更内容 |
|---------|---------|
| `services/dashboard/frontend/.dockerignore` | M-10: 新規作成 |

---

## 4. アーキテクチャ上の重要な変更点

### Brain の共有セッションパターン

```
Brain.run()
 └─ async with aiohttp.ClientSession() as session:
      ├─ LLMClient(session=session)
      ├─ DashboardClient(session=session)
      ├─ TaskReminder(session=session)
      └─ ToolExecutor(session=session)
```

全コンポーネントが単一の `ClientSession` を共有し、コネクションプーリングを活用。
テストスクリプト (`test_dedup_and_alerts.py` 等) は `DashboardClient()` を session なしで使用可能 (`_get_session()` フォールバック)。

### ReAct ループの新しいガード

```
cognitive_cycle():
  tool_call_history = []    # (name, args_hash) のリスト
  speak_count = 0           # サイクル内 speak 回数
  consecutive_errors = 0    # 連続エラー

  for i in range(REACT_MAX_ITERATIONS):
    -> 重複ツール呼出スキップ
    -> speak上限 (MAX_SPEAK_PER_CYCLE=1)
    -> 連続エラーでサイクル中断 (MAX_CONSECUTIVE_ERRORS=1)
```

### Sanitizer の新しい制御

```
speak:   ゾーン単位 5分クールダウン (_speak_history)
device:  swarm_hub* は常に許可、それ以外は allowed_devices チェック
task:    record_task_created() で事後記録 (※ H-5: タイミング修正が必要)
```

---

## 5. 並行作業に関する注意点

### 変更が競合しやすい領域

| ファイル | 理由 |
|---------|------|
| `services/brain/src/main.py` | 最も多くの改変が集中。cognitive_cycle, run, on_message 全てに変更あり |
| `infra/docker-compose.yml` | サービス追加・設定変更が頻繁 |
| `services/dashboard/frontend/src/App.tsx` | UI統合の集約点 |

### 並行開発で安全な領域

| 領域 | 理由 |
|------|------|
| `edge/` | ファームウェアは他サービスと独立 |
| `services/perception/` | Brain とは MQTT のみで接続。コード依存なし |
| `services/wallet/` | nginx 経由のREST APIのみ。他サービスのコードに依存なし |
| `docs/` | ドキュメントは並行編集可能 |
| `infra/virtual_edge/` | エミュレータは独立 |

### 現在の Docker ポートマップ

| ポート | サービス | 備考 |
|--------|---------|------|
| 80 | frontend (nginx) | 全API のエントリポイント |
| 1883/9001 | MQTT | Edge デバイス接続用 |
| 5432 | PostgreSQL | 127.0.0.1 のみ |
| 8000 | backend | 開発用直接アクセス |
| 8001 | mock-llm | 開発用 |
| 8002 | voice-service | 開発用 |
| 11434 | ollama | GPU LLM |
| 50021 | voicevox | TTS エンジン |

---

## 6. 残作業の優先度と推奨担当分け

### 即時対応 (独立して着手可能)

| タスク | 推奨担当 | 依存 |
|--------|---------|------|
| H-5: Sanitizer レート制限修正 | Worker A (Brain 担当) | なし |
| H-6: WalletBadge setState 修正 | Worker B (Frontend 担当) | なし |
| M-5: Perception network_mode 整理 | Worker C (Infra 担当) | なし |
| M-7: Voice Task モデル拡張 | Worker D (Voice 担当) | なし |
| L-1〜L-8: 低優先度クリーンアップ | 任意 | なし |

### HANDOFF.md の更新

現在の `HANDOFF.md` (プロジェクトルート) は Session F 時点の情報で古い。
このドキュメント (`docs/handoff/CURRENT_STATE.md`) が最新状態を反映している。

---

## 7. 環境情報

| 項目 | 値 |
|------|-----|
| OS | Linux 6.17.0-14-generic |
| CPU | AMD Ryzen 7 9800X3D |
| dGPU | RX 9700 (RDNA4, card1/renderD128) |
| iGPU | Raphael (card2/renderD129, ディスプレイ専用) |
| Docker グループ | sin ユーザー所属済み (sudo不要) |
| LLM | ollama qwen2.5:14b @ localhost:11434 |
| TTS | VOICEVOX speaker 47 |
| .env LLM_API_URL | `http://host.docker.internal:11434/v1` |
