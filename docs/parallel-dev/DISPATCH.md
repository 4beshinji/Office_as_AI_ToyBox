# Worker Dispatch — 2026-02-13 Session I

全ワーカーは作業開始前にこのファイルと [WORKER_GUIDE.md](./WORKER_GUIDE.md) を読むこと。

---

## 現在の main HEAD

```
c0467ac docs: add parallel development worker guide and API contracts
e07602e feat: add task completion report with status and MQTT broadcast
98c322f docs: add wallet separation design and session H handoff
```

## ブランチ状態サマリー

| ブランチ | main +N | 状態 | 備考 |
|---------|---------|------|------|
| `lane/L4-error-boundary-and-users` | +1 | **作業中** | ErrorBoundary 完了 + Users CRUD / kiosk accept が stash 中 |
| `lane/L3-voice-model-and-fixes` | +1 | **要リセット** | L4 コミット混入。main から再作成すべき |
| `lane/L4-dashboard-improvements` | +0 | **廃止** | 空。`L4-error-boundary-and-users` に統合済み |
| `lane/L7-infra-cleanup` | +0 | **未着手** | main と同一 |

## stash 情報

```
stash@{0}: On lane/L4-error-boundary-and-users: L4-worker-in-progress: users CRUD, kiosk accept, component cleanup
```

L4 ワーカーの作業途中。`git stash pop` で復元可能。

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

### L3 — Voice Service (要ブランチ再作成)

**優先度**: 高 (M-7 対応)
**ブランチ修正手順**:
```bash
git branch -D lane/L3-voice-model-and-fixes   # 汚染ブランチ削除
git checkout -b lane/L3-voice-model-and-fixes main
```

**タスク**:
1. **M-7 対応**: Voice Service の Task モデル拡張 (`services/voice/src/models.py`)
   - Dashboard の TaskCreate スキーマと整合させる (urgency, zone, bounty_gold 等)
   - `speech_generator.py` が拡張フィールドを活用するよう更新
2. Rejection stock の品質向上 (LLM プロンプト調整)
3. VOICEVOX speaker バリエーション検討

**注意**: `services/brain/`, `services/dashboard/` には触れない。API レスポンス形式は [API_CONTRACTS.md](./API_CONTRACTS.md) §3 を遵守。

---

### L4 — Dashboard (作業中 → 継続)

**優先度**: 高
**ブランチ**: `lane/L4-error-boundary-and-users` (既存)

**復帰手順**:
```bash
git checkout lane/L4-error-boundary-and-users
git stash pop
```

**完了済み**:
- [x] React Error Boundary (`acfd450`)
- [x] (stash) Users CRUD 完成 (GET/{id}, PUT/{id}, ページネーション, IntegrityError 処理)
- [x] (stash) TaskAccept の user_id を Optional 化 (anonymous kiosk 対応)
- [x] (stash) 不要コンポーネント削除 (UserSelector, WalletBadge, WalletPanel)

**残タスク**:
1. stash を pop してコミット
2. **レーン違反修正**: `queue_manager.py` の変更は L6 に委譲するか revert する
   - 該当: `dashboard._get_session()` への変更 → L6 が `services/brain/` で対応すべき
3. App.tsx の統合確認 (削除コンポーネントの参照が残っていないか)
4. Frontend ビルド確認: `npm run build`

**注意**: `services/wallet/`, `services/brain/` には触れない。`queue_manager.py` の変更は L6 向けに別途 PR/パッチ化すること。

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

### L6 — Brain (未着手)

**優先度**: 高 (H-5 対応)
**ブランチ**: `git checkout -b lane/L6-brain-fixes main`

**タスク**:
1. **H-5 対応**: `sanitizer.py:56-65` のレート制限タイミング修正
   - `record_task_created()` をバリデーション成功後に移動
2. `queue_manager.py` の ephemeral session 修正 (L4 が発見した問題)
   - `aiohttp.ClientSession()` → `self.dashboard._get_session()` に変更
3. task_report イベント受信後の Brain 反応ロジック検討
   - WorldModel にイベントは入る (`data_classes.py`) が LLM への反映はまだ
4. アクション履歴の LLM コンテキスト注入量チューニング

**注意**: 他の `services/` には触れない。MQTT 購読パターンの変更は WORKER_GUIDE の MQTT 表を更新すること。

---

### L7 — Infra / Docker (未着手 → 既存ブランチあり)

**優先度**: 中 (M-5 対応)
**ブランチ**: `lane/L7-infra-cleanup` (既存、main と同一)

**タスク**:
1. **M-5 対応**: Perception の `network_mode: host` と `networks:` の競合修正
   - `infra/docker-compose.yml:168` から perception の `networks:` を削除
2. **L-1〜L-8** 低優先度対応:
   - Dockerfile ベースイメージのタグ固定
   - 全サービスにヘルスチェック追加
   - 不要パッケージの整理
3. `docker-compose.yml` の検証: `docker compose config`
4. `.env.example` の更新 (新しい環境変数があれば追加)

**注意**: サービスのソースコードには触れない。他レーンから `docker-compose.yml` 変更依頼が来たら統合する。

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

### L9 — Mobile Wallet App / PWA (新規)

**優先度**: 高
**ブランチ**: `git checkout -b lane/L9-wallet-app main`

**技術スタック**: React 19 + TypeScript + Vite 6 + Tailwind CSS 4 + React Router 7 (PWA)
**ディレクトリ**: `services/wallet-app/` (スキャフォールド作成済み)

**スキャフォールド済み**:
- [x] `package.json`, `vite.config.ts`, `tsconfig.json`
- [x] `src/api/wallet.ts` — Wallet API クライアント (全エンドポイント型定義済み)
- [x] `public/manifest.json` — PWA マニフェスト
- [x] `src/App.tsx` — ルーター骨格 (placeholder)

**タスク**:
1. `npm install` で依存インストール
2. **Home ページ** (`src/pages/Home.tsx`)
   - 残高表示 (大きなフォント、SOMS 単位変換: balance / 1000)
   - 直近の取引 3 件
   - 供給量サマリー
3. **QR スキャンページ** (`src/pages/Scan.tsx`)
   - カメラアクセスで QR コード読み取り
   - QR ペイロード形式: `soms://reward?task_id={id}&amount={amount}`
   - `claimTaskReward()` API 呼出
4. **送金ページ** (`src/pages/Send.tsx`)
   - 宛先ユーザー ID 入力
   - 金額入力 + リアルタイム手数料プレビュー (`previewFee()`)
   - 確認 → `sendTransfer()` 実行
5. **履歴ページ** (`src/pages/History.tsx`)
   - 無限スクロール (offset ページネーション)
   - 取引タイプ別フィルタ
   - デビット/クレジット色分け
6. **共通コンポーネント**
   - `BottomNav.tsx` — タブナビゲーション (Home / Scan / Send / History)
   - `BalanceCard.tsx` — 残高表示カード
   - `TransactionItem.tsx` — 取引行コンポーネント
7. **ユーザー識別** — localStorage に user_id を保存 (初回起動時に入力 or QR から取得)

**API 依存** (全て `services/wallet-app/src/api/wallet.ts` に実装済み):
- `GET /api/wallet/wallets/{user_id}` — 残高
- `GET /api/wallet/wallets/{user_id}/history` — 履歴
- `GET /api/wallet/supply` — 供給量
- `GET /api/wallet/transactions/transfer-fee?amount=X` — 手数料プレビュー
- `POST /api/wallet/transactions/p2p-transfer` — P2P 送金
- `POST /api/wallet/transactions/task-reward` — QR 報酬受取

**モック方法**: Wallet Service が停止中でも `vite.config.ts` のプロキシ先を変更して MSW 等でスタブ可能。

**注意**:
- `services/wallet/` (バックエンド) には触れない。API 契約は `API_CONTRACTS.md` §2 準拠。
- `services/dashboard/` には触れない。コード共有なし。
- 決闘 (NFC/BLE) は MVP スコープ外。設計確定後に Capacitor 化を検討。

---

## レーン間の依存関係

```
L4 (stash pop + commit) ──→ L6 (queue_manager.py 修正を引き取る)
L3 (Voice model 拡張)   ──→ L6 (Brain が新フィールドを活用するなら)
L7 (docker-compose 修正) ──→ L2 (Perception の network_mode 修正後にテスト)
L9 (Wallet App)          ──→ L5 (Wallet API が安定していれば独立開発可能)
```

## マージ順序 (推奨)

1. **L7** — docker-compose は全サービスに影響。最初にマージ。
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
