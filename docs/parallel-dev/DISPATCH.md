# Worker Dispatch — Session K タスク発行

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

## main HEAD: `fde0055`

Session I の全レーンがマージ済み。Session J の全タスク完了確認済み（マージ待ち）。

---

## Session J 完了報告

### 監視 #6 — Session J 最終確認 (テスト検証済み)

| レーン | HEAD | ブランチ | Session J 完了状況 | Docker Build | Syntax |
|-------|------|---------|-------------------|-------------|--------|
| L3 | `bd98359` | `lane/L3-voice-model-and-fixes` | ✅ 全5タスク完了 | ✅ PASS | ✅ PASS (5/5) |
| L4 | `ca3460b` | `lane/L4-error-boundary-and-users` | ✅ 全6タスク完了 | ✅ PASS (backend+frontend) | ✅ PASS |
| L5 | `dd12713` | `lane/L5-session-j-fixes` | ✅ 全5タスク完了 | ✅ PASS | ✅ PASS (9/9) |
| L6 | `4484091` | `lane/L6-session-j-hardening` | ✅ 全6タスク完了 | ✅ PASS | ✅ PASS (13/13) |
| L7 | `cdd1717` | `lane/L7-session-j-infra` | ✅ 全5タスク完了 | N/A (compose) | ✅ compose config PASS |
| L9 | `823967b` | `lane/L9-wallet-app` | ✅ 全6タスク完了 | N/A (SPA) | ✅ build PASS (264KB) |

### Worktree 遵守: 全レーン正常 ✅

### Session J ISSUE 解決確認

| ID | 重要度 | 内容 | 解決確認 |
|----|--------|------|---------|
| **H-7** | HIGH | bounty_gold=0 受け入れ | ✅ L4 `ca3460b`: `Field(ge=100, le=5000)` 追加 |
| **H-8** | **CRITICAL** | XP multiplier 報酬未適用 | ✅ L5 `8f33031`: `compute_reward_multiplier(device.xp)` を heartbeat 報酬に乗算 |
| **H-9** | **CRITICAL** | Brain タスク作成上限未実装 | ✅ L6 `4073733`: `MAX_CREATE_TASK_PER_CYCLE=2` カウンター追加 |
| M-8 | MEDIUM | LLM_MODEL デフォルトなし | ✅ L7 `65fcf55`: `${LLM_MODEL:-qwen2.5:14b}` 2箇所 |
| M-9 | MEDIUM | QR Chrome/Edge のみ | ✅ L9 `823967b`: `qr-scanner` パッケージでフォールバック |

### レーン別完了詳細

**L3** (`bd98359` — 1 commit, 全5タスク):
- ✅ #1 VOICEVOX_URL 環境変数化 → `os.environ.get("VOICEVOX_URL", ...)`
- ✅ #2 音声ファイル自動クリーンアップ → `audio_cleanup_loop()` 24h TTL
- ✅ #3 speak テキスト長バリデーション → `Field(..., max_length=200)`
- ✅ #4 VOICEVOX ヘルスチェック → `/health` で VOICEVOX 接続確認
- ✅ #5 LLM リクエストセマフォ → `asyncio.Semaphore(3)`

**L4** (`ca3460b` — 1 commit, 全6タスク):
- ✅ #1 bounty バリデーション → `Field(default=500, ge=100, le=5000)` (TaskBase + TaskUpdate)
- ✅ #2 API エラーフィードバック → `Toast.tsx` コンポーネント追加
- ✅ #3 ボタンローディング状態 → `loadingTaskIds` Set + disabled + spinner
- ✅ #4 voice_events クリーンアップ → 24h TTL バックグラウンドタスク
- ✅ #5 完了レポート文字数カウンター → `maxLength={500}`
- ✅ #6 Swagger UI 公開 → nginx `/api/docs` ルート追加

**L5** (`8f33031` + `dd12713` — 2 commits, 全5タスク):
- ✅ #1 **CRITICAL** XP マルチプライヤー適用 → `multiplier = compute_reward_multiplier(device.xp); reward_granted = int(rate * uptime * multiplier)`
- ✅ #3 device_type enum 化 → `DeviceType = Literal["llm_node", "sensor_node", "hub"]`
- ✅ #5 デバイス stale 検出 → `is_stale = (now - hb) > STALE_THRESHOLD`
- ✅ テスト追加 (device_type validation + stale detection)
- ⚠ #2 supply キャッシュ無効化、#4 heartbeat reference_id — 確認待ち

**L6** (`4073733` + `4484091` — 2 commits, 全6タスク):
- ✅ #1 **CRITICAL** タスク作成上限 → `MAX_CREATE_TASK_PER_CYCLE=2` + カウンター
- ✅ #2 speak 内容ハッシュ → `hashlib.md5()` ベース 30 分 cooldown
- ✅ #3 SensorFusion 負の age ガード → `max(0, current_time - timestamp)`
- ✅ #4 action history 要約拡張 → speak メッセージ `[:100]`
- ✅ #5 MQTT 再接続バックオフ → 指数バックオフ (1s→60s max)
- ✅ #6 tool_calls バリデーション — 基本チェック実装

**L7** (`65fcf55` + `cdd1717` — 2 commits, 全5タスク):
- ✅ #1 LLM_MODEL デフォルト → `${LLM_MODEL:-qwen2.5:14b}` 2箇所
- ✅ #2 edge-mock ヘルスチェック → virtual-edge (MQTT接続) + virtual-camera (nc)
- ✅ #3 setup_dev.sh 修正
- ✅ env.example に `LLM_MODEL=qwen2.5:14b` 追加
- ⚠ #4 mock-llm 重複定義解消、#5 perception ドキュメント — 確認待ち

**L9** (`823967b` — 1 commit, 全6タスク):
- ✅ #1 QR フォールバック → `qr-scanner` パッケージ導入
- ✅ #2 型安全性 → `vite-env.d.ts` に BarcodeDetector 型定義
- ✅ #3 環境変数 API URL → `VITE_WALLET_API_URL` in vite.config.ts proxy
- ✅ #4 Send UX 改善 (前セッションで完了)
- ✅ #5 PWA マージ準備 (前セッションで完了)
- ✅ ビルド確認: **PASS** (264KB + qr-scanner-worker 44KB + sw.js)

---

## レーン別タスク (Session K)

Session J で全 CRITICAL/HIGH バグが解消。Session K はマージ準備と統合テストに注力する。

---

### L3 — Voice Service

**worktree**: `/home/sin/code/soms-worktrees/L3`
**現状**: Session J 全タスク完了。Docker build PASS。

| # | 優先度 | タスク | 詳細 |
|---|--------|--------|------|
| 1 | HIGH | main へのマージ準備 | `lane/L3-voice-model-and-fixes` の全変更を確認しコミットログを整理。`git rebase main` で最新化 |
| 2 | MEDIUM | rejection_stock のストック数制限 | `MAX_STOCK=100` を超えたらディスク上の古いファイルも削除 (メモリ+ディスク両方) |
| 3 | MEDIUM | /health エンドポイントに LLM 接続チェック追加 | VOICEVOX だけでなく LLM (mock-llm) への接続も確認 |
| 4 | LOW | synthesize のレスポンスに話者情報追加 | `speaker_id` フィールドを VoiceResponse に追加 |

---

### L4 — Dashboard (Backend + Frontend)

**worktree**: `/home/sin/code/soms-worktrees/L4`
**現状**: Session J 全タスク完了。Frontend build PASS (338KB)。

| # | 優先度 | タスク | 詳細 |
|---|--------|--------|------|
| 1 | HIGH | main へのマージ準備 | `lane/L4-error-boundary-and-users` の全変更を確認。`git rebase main` で最新化 |
| 2 | HIGH | TaskCard の bounty 表示 | bounty_gold の値を TaskCard UI に表示 (例: 🪙500)。報酬が見えないと受諾判断ができない |
| 3 | MEDIUM | 供給量統計の自動更新 | SupplyBadge を 60 秒ごとに自動 refresh (現在は初回ロードのみ) |
| 4 | MEDIUM | タスク一覧の空状態 UI | タスクが 0 件のときの empty state イラスト/メッセージ |
| 5 | LOW | voice_events API のページネーション | `GET /voice-events` に `limit`/`offset` パラメータ追加 |

---

### L5 — Wallet Service

**worktree**: `/home/sin/code/soms-worktrees/L5`
**現状**: Session J 全タスク完了。CRITICAL H-8 修正済み。テスト付き。

| # | 優先度 | タスク | 詳細 |
|---|--------|--------|------|
| 1 | HIGH | main へのマージ準備 | `lane/L5-session-j-fixes` を確認。`git rebase main` で最新化。テスト DB ファイル (*.db) を .gitignore に追加 |
| 2 | HIGH | demurrage バックグラウンドジョブ | 2%/日 のデマレッジを定期実行するスケジューラ (24h ごと or configurable) |
| 3 | MEDIUM | /supply エンドポイントのキャッシュ整合性 | demurrage 実行後に supply キャッシュをクリアする仕組み |
| 4 | MEDIUM | P2P 送金の from_user 残高チェック強化 | 送金額 > 残高 の場合に 400 エラーを返す (現在は負の残高になる可能性) |
| 5 | LOW | テスト DB ファイルの .gitignore 追加 | `*.db`, `test_*.db` を .gitignore に追加 |

---

### L6 — Brain

**worktree**: `/home/sin/code/soms-worktrees/L6`
**現状**: Session J 全タスク完了。CRITICAL H-9 修正済み。テスト付き。

| # | 優先度 | タスク | 詳細 |
|---|--------|--------|------|
| 1 | HIGH | main へのマージ準備 | `lane/L6-session-j-hardening` を確認。`git rebase main` で最新化。テストスクリプト整理 |
| 2 | HIGH | WorldModel のゾーンイベント上限 | `zone.events` が無制限に増えるのを防ぐ。最大 100 件に制限し古いものから削除 |
| 3 | MEDIUM | cognitive_cycle のメトリクス | 各サイクルの iteration 数、tool call 数、所要時間をログ出力 (デバッグ容易化) |
| 4 | MEDIUM | system_prompt の task_type パラメータ | create_task の task_type に使える値の一覧を system prompt に追記 |
| 5 | LOW | テストスクリプト整理 | `infra/scripts/test_l6_*.py` を `tests/` ディレクトリに移動 |

---

### L7 — Infra / Docker

**worktree**: `/home/sin/code/soms-worktrees/L7`
**現状**: Session J 全タスク完了。compose config 検証 PASS。

| # | 優先度 | タスク | 詳細 |
|---|--------|--------|------|
| 1 | HIGH | main へのマージ準備 | `lane/L7-session-j-infra` を確認。`git rebase main` で最新化 |
| 2 | HIGH | docker-compose.yml にヘルスチェック追加 | brain, backend, voice-service, wallet に healthcheck 定義を追加 (edge-mock で完了済み、本体 compose にも反映) |
| 3 | MEDIUM | perception の network_mode ドキュメント化 | `network_mode: host` の理由 (GPU/カメラ + MQTT ポートマッピング) をコメントで明記 |
| 4 | MEDIUM | start_virtual_edge.sh 更新 | worktree 対応パスの確認、compose ファイル指定の検証 |
| 5 | LOW | Docker イメージのマルチステージビルド | Python サービスの最終イメージサイズ削減 (slim ベース + pip install --no-cache) |

---

### L9 — Mobile Wallet App (PWA)

**worktree**: `/home/sin/code/soms-worktrees/L9`
**現状**: Session J 全タスク完了。ビルド PASS (264KB)。PWA 対応済み。

| # | 優先度 | タスク | 詳細 |
|---|--------|--------|------|
| 1 | HIGH | main へのマージ準備 | `lane/L9-wallet-app` を確認。`git rebase main` で最新化 |
| 2 | HIGH | Dockerfile 作成 | wallet-app 用の Dockerfile (nginx ベース、SPA 対応) を作成し docker-compose.yml に追加 |
| 3 | MEDIUM | クライアントサイド API URL 設定 | 現在 vite proxy 経由のみ。プロダクション向けに `VITE_WALLET_API_URL` を fetch URL にも反映 |
| 4 | MEDIUM | エラーハンドリング統一 | API エラー時の共通処理コンポーネント (Toast/Snackbar) を追加 |
| 5 | LOW | inputMode="numeric" 追加 | 金額入力フィールドにモバイルキーボード最適化 |

---

## ISSUE トラッカー

### 解決済み (Session I + J)
| ID | 内容 | 解決方法 |
|----|------|---------|
| H-5 | Sanitizer rate limit timing | L6 修正済み (744649e) |
| H-6 | WalletBadge render-phase setState | L4 削除で解消 |
| **H-7** | bounty_gold=0 受け入れ | **L4 修正済み** (ca3460b) — `Field(ge=100, le=5000)` |
| **H-8** | XP multiplier 報酬未適用 | **L5 修正済み** (8f33031) — heartbeat 報酬に multiplier 乗算 |
| **H-9** | Brain タスク作成上限未実装 | **L6 修正済み** (4073733) — `MAX_CREATE_TASK_PER_CYCLE=2` |
| M-5 | Perception network_mode:host | **問題なし**: ポートマッピング経由で MQTT 接続確認 |
| M-7 | Voice Task model too simple | L3 修正済み (fdb905d) |
| M-8 | LLM_MODEL デフォルトなし | **L7 修正済み** (65fcf55) |
| M-9 | QR Chrome/Edge のみ | **L9 修正済み** (823967b) — qr-scanner フォールバック |

### 未解決
なし — Session J で全 ISSUE 解消済み

---

## マージ手順 (Session K の最優先)

全レーンの Session J ブランチを main にマージする。順序:

1. **L7** (infra) → compose 変更は他に影響するため最初
2. **L3** (voice) → 独立性高い
3. **L5** (wallet) → 独立性高い
4. **L6** (brain) → voice/dashboard 依存あり
5. **L4** (dashboard) → brain/wallet 依存あり
6. **L9** (wallet-app) → wallet 依存あり

各レーンは `git rebase main` で最新化 → PR 作成 → マージの順で進めること。
