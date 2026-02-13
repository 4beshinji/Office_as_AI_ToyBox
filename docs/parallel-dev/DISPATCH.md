# Worker Dispatch — Session J タスク発行

全ワーカーは作業開始前にこのファイルと [WORKER_GUIDE.md](./WORKER_GUIDE.md) を読むこと。

## ✅ Worktree 導入済み

| レーン | worktree パス | ブランチ |
|-------|--------------|---------|
| Main | `/home/sin/code/Office_as_AI_ToyBox` | `main` |
| L3 | `/home/sin/code/soms-worktrees/L3` | `lane/L3-*` |
| L4 | `/home/sin/code/soms-worktrees/L4` | `lane/L4-*` |
| L5 | `/home/sin/code/soms-worktrees/L5` | `lane/L5-*` |
| L6 | `/home/sin/code/soms-worktrees/L6` | `lane/L6-*` |
| L7 | `/home/sin/code/soms-worktrees/L7` | `lane/L7-*` |
| L9 | `/home/sin/code/soms-worktrees/L9` | `lane/L9-*` |

**ルール**: メインディレクトリで `git checkout` 禁止。各自の worktree パスで作業すること。
新ブランチ作成時は worktree 内で `git checkout -b lane/L{N}-new-description` を実行。

## main HEAD: `f861b7d`

Session I の全レーンがマージ済み。全サービス healthy 稼働確認済み。
受け入れ基準テスト全 PASS (Docker build, frontend build, API 動作, Brain ReAct loop)。

---

## レーン別タスク (Session J)

各ワーカーは自分のレーンのタスクを **優先度順** に処理すること。
テスト確認済みのバグ・ギャップに基づく具体的な指示。

---

### L3 — Voice Service

**worktree**: `/home/sin/code/soms-worktrees/L3`
**現状**: API 100% 実装済み、rejection stock 動作中 (80/100)、synthesize 正常 (0.74s)

| # | 優先度 | タスク | 詳細 |
|---|--------|--------|------|
| 1 | HIGH | VOICEVOX_URL 環境変数化 | `voicevox_client.py:35` の `http://voicevox:50021` をハードコードから `os.environ.get("VOICEVOX_URL", "http://voicevox:50021")` に変更 |
| 2 | HIGH | 音声ファイル自動クリーンアップ | `/app/audio/` 配下の 24 時間以上経過したファイルを定期削除するバックグラウンドタスク追加 |
| 3 | MEDIUM | speak テキスト長バリデーション | `SynthesizeRequest.text` に `max_length=200` 制約追加 (VOICEVOX 負荷防止) |
| 4 | MEDIUM | VOICEVOX ヘルスチェック追加 | `/health` エンドポイントで VOICEVOX 接続確認、失敗時は `503` を返す |
| 5 | LOW | LLM リクエストセマフォ | `speech_generator.py` の `_call_llm()` に `asyncio.Semaphore(3)` を追加し同時リクエスト制限 |

---

### L4 — Dashboard (Backend + Frontend)

**worktree**: `/home/sin/code/soms-worktrees/L4`
**現状**: frontend build OK (333KB)、backend healthy、Task CRUD 動作確認済み

| # | 優先度 | タスク | 詳細 |
|---|--------|--------|------|
| 1 | HIGH | bounty バリデーション追加 | `schemas.py` の `TaskBase` に `bounty_gold: int = Field(ge=100, le=5000)` 制約追加。**テスト確認済み**: bounty_gold=0 のタスクが受け入れられている |
| 2 | HIGH | API エラーのユーザーフィードバック | accept/complete 失敗時にトースト通知を表示。現在は console.error のみ |
| 3 | HIGH | ボタンローディング状態 | Accept/Complete ボタンに disabled + spinner を追加。連打による重複リクエスト防止 |
| 4 | MEDIUM | voice_events クリーンアップ | 24 時間以上前の VoiceEvent をバックグラウンドで削除するタスク追加 (DB 肥大化防止) |
| 5 | MEDIUM | 完了レポートの文字数カウンター | completion_note textarea に `XXX/500` カウンター表示 |
| 6 | LOW | Swagger UI 公開 | nginx.conf に `/api/docs` → `backend:8000/docs` ルート追加 |

---

### L5 — Wallet Service

**worktree**: `/home/sin/code/soms-worktrees/L5`
**現状**: double-entry 動作確認済み、P2P 5% burn 確認済み、supply stats 正常

| # | 優先度 | タスク | 詳細 |
|---|--------|--------|------|
| 1 | **CRITICAL** | XP マルチプライヤーを報酬に適用 | `routers/devices.py` の heartbeat reward 計算に `compute_reward_multiplier(device.xp)` を乗算。**テスト確認済み**: 現在 multiplier は GET endpoint のみで計算され、実際の報酬には未適用 |
| 2 | HIGH | supply キャッシュの demurrage 後無効化 | バックグラウンド demurrage 実行後に supply キャッシュをクリア。現在 60 秒間 stale データを返す可能性 |
| 3 | HIGH | device_type の enum 化 | `DeviceCreate` スキーマに `Literal["llm_node", "sensor_node", "hub"]` バリデーション追加 |
| 4 | MEDIUM | heartbeat reference_id の衝突防止 | UUID を含めるよう変更: `f"infra:{device_id}:{uuid4().hex[:8]}"` |
| 5 | MEDIUM | デバイス stale 検出 | `last_heartbeat_at` が 2 時間以上前のデバイスを `GET /devices` で `is_stale: true` 表示 |

---

### L6 — Brain

**worktree**: `/home/sin/code/soms-worktrees/L6`
**現状**: ReAct ループ正常 (25s 間隔、1-2/5 iterations)、タスク作成・音声連携確認済み

| # | 優先度 | タスク | 詳細 |
|---|--------|--------|------|
| 1 | **CRITICAL** | サイクルあたりタスク作成上限 | `cognitive_cycle()` 内にカウンターを追加し、`create_task` を 2 回/cycle に制限。**確認済み**: 現在コードレベルの制限なし (system prompt のみ) |
| 2 | HIGH | speak メッセージ内容ハッシュ | Sanitizer に `hashlib.md5(message)` ベースの cooldown 追加。同一内容の繰り返しを 30 分間ブロック |
| 3 | HIGH | SensorFusion 負の age_seconds ガード | `sensor_fusion.py` で `age_seconds = max(0, age_seconds)` を追加。時刻ズレによる異常重み付け防止 |
| 4 | MEDIUM | action history 要約文字数拡張 | speak メッセージの切り詰めを 30→100 文字に拡張。LLM が過去の発言を正確に把握するために必要 |
| 5 | MEDIUM | MQTT 再接続バックオフ | 接続失敗時に指数バックオフ (1s, 2s, 4s, 8s, max 60s) で再試行するループ追加 |
| 6 | LOW | LLM レスポンスの tool_calls 構造バリデーション | `llm_client.py` で tool name, arguments の型チェック追加 |

---

### L7 — Infra / Docker

**worktree**: `/home/sin/code/soms-worktrees/L7`
**現状**: compose config 検証 OK、全 11 サービス healthy、ポート衝突なし

| # | 優先度 | タスク | 詳細 |
|---|--------|--------|------|
| 1 | HIGH | LLM_MODEL のデフォルト値追加 | `docker-compose.yml` で `LLM_MODEL=${LLM_MODEL:-qwen2.5:14b}` に変更。brain, voice-service の 2 箇所。**確認済み**: 現在 .env 未設定時に空文字で起動する |
| 2 | HIGH | edge-mock compose にヘルスチェック追加 | `virtual-edge`, `virtual-camera` に healthcheck 定義追加 |
| 3 | MEDIUM | setup_dev.sh のボリューム名修正 | `soms_db_data` → `soms_pg_data` に修正 (compose と一致させる) |
| 4 | MEDIUM | mock-llm の重複定義解消 | `docker-compose.edge-mock.yml` から mock-llm を削除 (メイン compose にのみ定義) |
| 5 | LOW | perception の network_mode ドキュメント化 | `network_mode: host` が必要な理由 (GPU/カメラアクセス) と MQTT がポートマッピング経由で接続する仕組みをコメントで明記 |

**M-5 再評価**: ~~Perception network_mode:host と networks: の競合~~ → **問題なし**。
perception は host ネットワークから `localhost:1883` (ポートマッピング経由) で MQTT 接続成功確認済み。

---

### L9 — Mobile Wallet App (PWA)

**worktree**: `/home/sin/code/soms-worktrees/L9`
**現状**: 4 ページ実装済み、API 統合完了、frontend build OK (246KB)

| # | 優先度 | タスク | 詳細 |
|---|--------|--------|------|
| 1 | HIGH | QR スキャナーフォールバック追加 | `jsQR` または `qr-scanner` パッケージ追加。BarcodeDetector 非対応ブラウザ (Firefox/Safari) で動作させる |
| 2 | HIGH | Scan.tsx の型安全性修正 | `vite-env.d.ts` に BarcodeDetector の型定義追加、`as unknown` キャスト除去 |
| 3 | HIGH | 環境変数ベースの API URL | `vite.config.ts` のプロキシ URL を `VITE_WALLET_API_URL` 環境変数から取得するよう変更 |
| 4 | MEDIUM | Send ページの UX 改善 | 送金ボタンにスピナー追加、成功メッセージの 3 秒後自動消去、「もう一度送る」ボタン |
| 5 | MEDIUM | PWA ブランチの main マージ準備 | L9 worktree の未コミット変更をコミット、eslint.config.js を追跡対象に追加 |
| 6 | LOW | inputMode ヒント追加 | 金額入力に `inputMode="numeric"` 設定 |

---

## ISSUE トラッカー

### 解決済み
| ID | 内容 | 解決方法 |
|----|------|---------|
| H-5 | Sanitizer rate limit timing | L6 修正済み (744649e) |
| H-6 | WalletBadge render-phase setState | L4 削除で解消 |
| M-5 | Perception network_mode:host | **問題なし**: ポートマッピング経由で MQTT 接続確認 |
| M-7 | Voice Task model too simple | L3 修正済み (fdb905d) |

### 新規発見 (Session J テスト)
| ID | 重要度 | 内容 | 担当 |
|----|--------|------|------|
| H-7 | HIGH | bounty_gold=0 のタスクが受け入れられる | L4 |
| H-8 | HIGH | XP multiplier が報酬計算に未適用 | L5 |
| H-9 | HIGH | Brain のサイクル内タスク作成上限がコード未実装 | L6 |
| M-8 | MEDIUM | LLM_MODEL 環境変数デフォルトなし | L7 |
| M-9 | MEDIUM | QR スキャナーが Chrome/Edge のみ対応 | L9 |
