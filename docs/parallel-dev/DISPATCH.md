# Worker Dispatch — 2026-02-13 Session I (worktree 導入後)

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

## ブランチ状態 (監視 #3 + worktree 移行)

| ブランチ | +N | 状態 | 備考 |
|---------|---|------|------|
| L3 | +1 | worktree移行済 | voice model 拡張完了 |
| L4 | +2 | worktree移行済 | ErrorBoundary + Users CRUD 完了 |
| L5 | +0 | worktree移行済 | 起動確認、実作業未確認 |
| L6 | +4 | worktree移行済 | H-5修正 + task_report + action history |
| L7 | +3 | worktree移行済 | healthchecks + virtual_camera + env |
| L9 | +1 | worktree移行済 | wallet app 全ページ実装 |

## L6 コミット詳細
- f82633e feat(L3) ← 混入
- e0cdcb5 fix(L7) ← 混入
- 51df20c fix(L6): H-5 speak cooldown + queue_manager + dead code ← 本来

## L7 コミット詳細
- 6896c08 chore(L7): env vars ← 本来
- 84068c4 feat(L6): task_report ← 混入
- d9b0601 fix(L7): virtual_camera ← 本来
- 4af92c3 feat(L7): healthchecks ← 本来
- 52cd986 feat(L9): package-lock ← 混入
- 54391c1 feat(L3)+L9 ← 混入

## 復旧方針
1. L4: クリーン。rebase main のみ
2. L6: rebase -i で f82633e,e0cdcb5 drop → cherry-pick 84068c4
3. L7: rebase -i で 54391c1,52cd986,84068c4 drop
4. L3: L7 54391c1 から services/voice/ 回収
5. L9: L7 54391c1+52cd986 から services/wallet-app/ 回収

## レーン別タスク (詳細は上方のブランチ状態を参照)

- **L1-L2**: 未着手
- **L3**: Voice model回収 → rejection stock改善
- **L4**: rebase main → npm run build
- **L5**: 未着手
- **L6**: ブランチ整理 → LLM注入量チューニング
- **L7**: ブランチ整理 → M-5 perception network修正
- **L8**: 未着手
- **L9**: wallet-app回収 → npm run build → PWA SW
