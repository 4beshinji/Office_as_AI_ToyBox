# Worker Dispatch — 2026-02-13 Session I (監視 #4)

全ワーカーは作業開始前にこのファイルと [WORKER_GUIDE.md](./WORKER_GUIDE.md) を読むこと。

## ✅ Worktree 導入済み

Session I で発生した共有ワーキングツリー問題（ブランチ間作業混入）を解決するため、
**全レーンに永続 worktree を配置済み。** 詳細は WORKER_GUIDE.md を参照。

| レーン | worktree パス | ブランチ |
|-------|--------------|---------|
| Main | `/home/sin/code/Office_as_AI_ToyBox` | `main` |
| L3 | `/home/sin/code/soms-worktrees/L3` | `lane/L3-voice-model-and-fixes` |
| L4 | `/home/sin/code/soms-worktrees/L4` | `lane/L4-error-boundary-and-users` |
| L5 | `/home/sin/code/soms-worktrees/L5` | `lane/L5-wallet-integration-test` |
| L6 | `/home/sin/code/soms-worktrees/L6` | `lane/L6-brain-fixes` |
| L7 | `/home/sin/code/soms-worktrees/L7` | `lane/L7-infra-cleanup` |
| L9 | `/home/sin/code/soms-worktrees/L9` | `lane/L9-wallet-app` |

**ルール**: メインディレクトリで `git checkout` 禁止。各自の worktree パスで作業すること。

## main HEAD: `45e8e4b` — 全レーンマージ済み

main への統合が完了。マージ順序は WORKER_GUIDE.md 記載の通り:

1. `399ae95 merge(L7)` — healthchecks, depends_on, env, edge-mock ✅
2. `65a2059 merge(L4)` — ErrorBoundary, users CRUD, component cleanup ✅
3. `d1b019c merge(L6)` — H-5 speak cooldown, task_report, action history ✅
4. `a030a93 merge(L3)` — Voice Task model, rejection prompt, speaker variation ✅
5. `7fc9b47 merge(L5)` — heartbeat rewards, supply cache, demurrage, i18n ✅
6. `45e8e4b merge(L9)` — wallet PWA app 全ページ ✅

## ブランチ状態 (監視 #4)

| ブランチ | HEAD | 状態 | 未コミット変更 |
|---------|------|------|--------------|
| L3 | `70c4e7b` | main マージ済・クリーン | なし |
| L4 | `03961ab` | main マージ済・クリーン | なし |
| L5 | `226babf` | main マージ済・作業中 | database.py, main.py, models.py + test_integration.py |
| L6 | `46d5922` | main マージ済・作業中 | test_l6_brain_fixes.py (新規) |
| L7 | `b1d2722` | main マージ済・クリーン | なし |
| L9 | `7122b15` | main マージ済・作業中 | PWA改善 (manifest, icons, sw.js) |

## Worktree 遵守状況

- **L3**: ✅ worktree で作業、新コミット `70c4e7b` 完了
- **L4**: ✅ main にリベース後マージ、クリーン
- **L5**: ✅ worktree で作業中、新コミット + 追加変更進行中
- **L6**: ✅ worktree でテストスクリプト作成中
- **L7**: ✅ マージ完了、アイドル
- **L9**: ✅ worktree で PWA 改善作業中

### 違反履歴
- worktree 導入直後に 1 件の `git checkout` 違反 (main → L5-wallet-improvements)
- その後は全ワーカーが worktree を正しく使用中

## 残存課題

### ブランチ整理
- `lane/L5-wallet-improvements` — L9 混入コミットあり。マージ不要（L5 本流は `lane/L5-wallet-integration-test`）

### 未解決 ISSUES
- **M-5**: Perception network_mode:host と networks: の競合
- **L-1〜L-8**: 低優先度

## レーン別次タスク

- **L3**: マージ済。次タスクがあれば新ブランチ作成
- **L4**: マージ済。次タスクがあれば新ブランチ作成
- **L5**: 作業続行中 — heartbeat rewards テスト + DB 改善
- **L6**: テストスクリプト作成中
- **L7**: M-5 perception network 修正 or アイドル
- **L9**: PWA 改善続行中 (manifest, service worker, icons)
