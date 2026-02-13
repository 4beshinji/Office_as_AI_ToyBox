# Worker Dispatch — 2026-02-13 Session I

全ワーカーは作業開始前にこのファイルと [WORKER_GUIDE.md](./WORKER_GUIDE.md) を読むこと。

---

## 現在の main HEAD

```
c8cb90b feat(L9): scaffold mobile wallet PWA app with API client
478ae97 docs: add worker dispatch instructions and update current state
c0467ac docs: add parallel development worker guide and API contracts
e07602e feat: add task completion report with status and MQTT broadcast
```

## ⚠ 重大問題: 共有ワーキングツリーの競合

**複数のワーカーが同じ `.git` ディレクトリで同時に `git checkout` を実行しており、以下の問題が発生中**:

1. **ブランチ間作業混入**: L3/L9 の変更が L7 ブランチにコミットされている
2. **stash 消失**: L4 用に保存した stash が空になった
3. **未コミット変更の流出**: あるワーカーの変更が別ブランチにステージされる
4. **ファイルリバート**: ドキュメント更新が別ワーカーのチェックアウトで上書きされる

**全ワーカー必須対策**:
- コミット前に `git branch --show-current` でブランチ確認
- `git diff --cached --stat` でステージ内容が自レーンのファイルのみか確認
- 可能であれば `git worktree add` で独立ワーキングツリーを使用

## ブランチ状態サマリー (監視 #2)

| ブランチ | main +N/-N | 状態 | 備考 |
|---------|-----------|------|------|
| `lane/L3-voice-model-and-fixes` | +0/-0 | **リセット済** | main と同一。Voice 作業は L7 ブランチに混入 (後述) |
| `lane/L4-error-boundary-and-users` | +1/-2 | **中断** | ErrorBoundary 完了。stash 消失、Users CRUD 再実装が必要 |
| `lane/L6-brain-fixes` | +0/-0 | **作業開始** | sanitizer.py の H-5 修正が未コミット。ワーキングツリー競合で消失リスクあり |
| `lane/L7-infra-cleanup` | +3/-0 | **⚠ 要クリーンアップ** | 3コミット中2件は他レーン混入 (下記参照) |
| `lane/L9-wallet-app` | +0/-0 | **作業中** | ページ実装が L7 ブランチに混入。本ブランチにコミットなし |

### L7 ブランチ汚染の詳細

```
lane/L7-infra-cleanup (main +3):
  54391c1 feat(L3): expand Voice Task model + L9 wallet app ページ (15 files, +786/-32)  ← L3+L9 混入
  52cd986 feat(L9): implement wallet app pages — package-lock.json only (+3906)            ← L9 混入
  4af92c3 feat(L7): add healthchecks to all 11 Docker services (+70/-1)                    ← L7 本来の作業
```

**復旧方針**:
- L7: `4af92c3` のみ有効。新ブランチ作成して cherry-pick するか rebase -i で整理
- L3: `54391c1` から `services/voice/` ファイルのみ cherry-pick して L3 ブランチに移動
- L9: `54391c1` から `services/wallet-app/` ファイルのみ + `52cd986` を L9 ブランチに移動

## stash 情報

```
(空)
```

stash は消失済み。L4 ワーカーは Users CRUD を再実装する必要あり。

---

## 各レーン指示

### L1 — Edge / SensorSwarm (未着手)

**優先度**: 中
**ブランチ**: `git checkout -b lane/L1-swarm-improvements main`

**タスク**:
1. `edge/lib/swarm/` の BLE トランスポート実装 (`transport_ble.py`)
2. SensorSwarm Hub のヘルスチェック機能追加
3. `edge/tools/` 診断スクリプトのテスト・整備
4. `infra/virtual_edge/` エミュレータの SensorSwarm 対応

**注意**: `services/` には触れない。MQTT テレメトリ形式 `{"value": X}` を遵守。

---

### L2 — Perception (未着手)

**優先度**: 中
**ブランチ**: `git checkout -b lane/L2-perception-improvements main`

**タスク**:
1. ActivityMonitor のポーズバッファ改善 (tier 管理の効率化)
2. カメラ自動検出 (`camera_discovery.py`) の安定化
3. テストスクリプト (`test_activity.py`, `test_discovery.py`) の整備
4. `config/monitors.yaml` のスキーマバリデーション追加

**注意**: `services/brain/`, `services/dashboard/` には触れない。MQTT publish トピックは既存パターン準拠。

---

### L3 — Voice Service (L7 ブランチから作業を回収)

**優先度**: 高 (M-7 対応)
**状態**: L3 の作業が `lane/L7-infra-cleanup` の `54391c1` に混入済み

**復帰手順**:
```bash
git checkout lane/L3-voice-model-and-fixes
# L7 ブランチの混入コミットから voice ファイルのみ取り出す
git checkout 54391c1 -- services/voice/
git commit -m "feat(L3): expand Voice Task model, fix rejection stock race condition"
```

**完了済み** (L7 ブランチ `54391c1` にて):
- [x] Voice Task モデル拡張 (`models.py`)
- [x] Rejection stock レースコンディション修正 (`rejection_stock.py`)
- [x] Audio 定数抽出 (`speech_generator.py`)
- [x] main.py 更新

**残タスク**:
1. L3 ブランチに正しくコミットを移動 (上記手順)
2. Rejection stock の品質向上 (LLM プロンプト調整)
3. VOICEVOX speaker バリエーション検討

**注意**: `services/brain/`, `services/dashboard/` には触れない。API レスポンス形式は [API_CONTRACTS.md](./API_CONTRACTS.md) §3 を遵守。

---

### L4 — Dashboard (中断 → 再実装が必要)

**優先度**: 高
**ブランチ**: `lane/L4-error-boundary-and-users` (既存、main に 2 コミット遅れ)

**復帰手順**:
```bash
git checkout lane/L4-error-boundary-and-users
git rebase main    # dispatch docs + L9 scaffold を取り込む
```

**完了済み**:
- [x] React Error Boundary (`acfd450`)

**⚠ stash 消失 — 以下は再実装が必要**:
- [ ] Users CRUD (GET/{id}, PUT/{id}, ページネーション, IntegrityError 処理)
- [ ] TaskAccept の user_id を Optional 化 (anonymous kiosk 対応)
- [ ] 不要コンポーネント削除 (UserSelector, WalletBadge, WalletPanel)

**残タスク**:
1. `git rebase main` で最新化
2. Users CRUD 再実装
3. TaskAccept anonymous kiosk 対応
4. **レーン違反禁止**: `queue_manager.py` (brain) には触れない。L6 に委譲
5. Frontend ビルド確認: `npm run build`

**注意**: `services/wallet/`, `services/brain/` には触れない。

---

### L5 — Wallet Service (未着手)

**優先度**: 中
**ブランチ**: `git checkout -b lane/L5-wallet-improvements main`

**タスク**:
1. デマレッジスケジューラのテスト (`services/wallet/src/services/demurrage.py`)
2. Wallet API のエラーメッセージ国際化 (現在一部日本語のみ)
3. Supply stats のキャッシュ実装 (毎リクエストで DB クエリは非効率)
4. Device heartbeat → XP 自動付与ロジックの実装

**注意**: `services/dashboard/` には触れない。API 契約は [API_CONTRACTS.md](./API_CONTRACTS.md) §2 を遵守。

---

### L6 — Brain (作業開始 → 未コミット変更あり)

**優先度**: 高 (H-5 対応)
**ブランチ**: `lane/L6-brain-fixes` (既存、main と同一)

**作業中の変更** (未コミット、ワーキングツリー競合で消失リスクあり):
- `sanitizer.py`: `validate_action()` の speak cooldown 記録を `record_speak()` メソッドに分離
  - これは H-5 修正の一部 (バリデーション成功後にのみ記録する)

**タスク**:
1. **H-5 対応**: `sanitizer.py` のレート制限タイミング修正 ← 着手済み
   - `record_speak()` を `validate_action()` から分離 ← 完了 (要コミット)
   - `record_task_created()` も同様に分離する
   - `tool_executor.py` から成功時のみ `record_*()` を呼ぶ
2. `queue_manager.py` の ephemeral session 修正
   - `aiohttp.ClientSession()` → `self.dashboard._get_session()` に変更
3. task_report イベント受信後の Brain 反応ロジック検討
4. アクション履歴の LLM コンテキスト注入量チューニング

**⚠ 注意**: 未コミット変更は他ワーカーのブランチ切替で消失する可能性がある。こまめにコミットすること。他の `services/` には触れない。

---

### L7 — Infra / Docker (コミット済み → 要クリーンアップ)

**優先度**: 中 (M-5 対応)
**ブランチ**: `lane/L7-infra-cleanup` (main +3、うち2件は混入)

**完了済み**:
- [x] 全11サービスにヘルスチェック追加 (`4af92c3`)
- [x] mosquitto タグ固定 (`latest` → `2`)

**⚠ 要クリーンアップ**: ブランチに L3/L9 のコミットが混入。マージ前に整理が必要:
```bash
# 方法1: 新ブランチで L7 コミットのみ cherry-pick
git checkout -b lane/L7-infra-cleanup-clean main
git cherry-pick 4af92c3
git branch -m lane/L7-infra-cleanup-clean lane/L7-infra-cleanup

# 方法2: interactive rebase で不要コミットを除去
git checkout lane/L7-infra-cleanup
git rebase -i main  # 54391c1 と 52cd986 を drop
```

**残タスク**:
1. ブランチクリーンアップ (上記)
2. **M-5 対応**: Perception の `network_mode: host` と `networks:` の競合修正
3. Dockerfile ベースイメージのタグ固定
4. `docker-compose.yml` の検証: `docker compose config`
5. `.env.example` の更新

**注意**: サービスのソースコードには触れない。

---

### L8 — Docs (未着手)

**優先度**: 低
**ブランチ**: `git checkout -b lane/L8-docs-update main`

**タスク**:
1. `README.md` の更新 (プロジェクト概要、Quick Start)
2. `docs/SYSTEM_OVERVIEW.md` への task_report フロー追記
3. `DEPLOYMENT.md` の作成 (ROCm 6.x + Docker 環境構築手順)
4. `docs/handoff/CURRENT_STATE.md` を Session I の状態に更新

**注意**: ソースコードには触れない。

---

### L9 — Mobile Wallet App / PWA (作業中 → L7 ブランチから回収)

**優先度**: 高
**ブランチ**: `lane/L9-wallet-app` (既存、main と同一)
**状態**: ページ実装が `lane/L7-infra-cleanup` の `54391c1` + `52cd986` に混入

**回収手順**:
```bash
git checkout lane/L9-wallet-app
# L7 ブランチから wallet-app ファイルを取り出す
git checkout 54391c1 -- services/wallet-app/
git checkout 52cd986 -- services/wallet-app/package-lock.json
git commit -m "feat(L9): implement wallet app pages — Home, Send, History, QR Scan"
```

**完了済み** (L7 ブランチに混入):
- [x] Home ページ (`Home.tsx`)
- [x] 送金ページ (`Send.tsx`)
- [x] 履歴ページ (`History.tsx`)
- [x] QR スキャンページ (`Scan.tsx`)
- [x] 共通コンポーネント (BalanceCard, BottomNav, TransactionItem)
- [x] useUserId フック
- [x] App.tsx ルーティング更新
- [x] package-lock.json (npm install 済み)

**残タスク**:
1. L9 ブランチに正しくコミットを移動 (上記手順)
2. TypeScript ビルド確認: `npm run build`
3. 実機テスト (Wallet Service 起動状態で)
4. PWA オフライン対応 (Service Worker)

**注意**:
- `services/wallet/` (バックエンド) には触れない。API 契約は `API_CONTRACTS.md` §2 準拠。
- `services/dashboard/` には触れない。コード共有なし。
- 決闘 (NFC/BLE) は MVP スコープ外。

---

## レーン間の依存関係

```
L4 (rebase + 再実装) ──→ L6 (queue_manager.py 修正を引き取る)
L3 (回収 + 継続)      ──→ L6 (Brain が新フィールドを活用するなら)
L7 (クリーンアップ)   ──→ L2 (Perception の network_mode 修正後にテスト)
L9 (回収 + 継続)      ──→ L5 (Wallet API が安定していれば独立開発可能)
```

## マージ順序 (推奨)

1. **L7** — docker-compose は全サービスに影響。**ブランチクリーンアップ後に**最初にマージ。
2. **L4** — ErrorBoundary + Users CRUD + kiosk accept。
3. **L6** — H-5 修正 + queue_manager + task_report 活用。L4 の後。
4. **L3** — Voice model 拡張。独立。
5. **L5** — Wallet 改善。独立。
6. **L9** — Wallet App。L5 と同時マージ可能 (API 契約変更がなければ)。
7. **L1, L2** — Edge/Perception。独立。
8. **L8** — 最後にドキュメント更新。

---

## 共通ルール (再掲)

- `WORKER_GUIDE.md` のファイル所有権マトリクスを厳守
- 他レーンのファイルを変更する必要がある場合、**別コミットで分離**し PR 説明に明記
- コミットメッセージは `{type}(L{N}): {description}` 形式
- ブランチ名は `lane/L{N}-{description}` 形式
- **コミット前に必ず `git branch --show-current` でブランチを確認**
- **`git diff --cached --stat` でステージ内容が自レーンのファイルのみか確認**
