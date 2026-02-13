# Worker Dispatch — 2026-02-13 Session I (監視 #3)

全ワーカーは作業開始前にこのファイルと [WORKER_GUIDE.md](./WORKER_GUIDE.md) を読むこと。

## ⚠ 重大問題: 共有ワーキングツリーの競合

複数ワーカーが同じ .git で git checkout を同時実行。ブランチ間で作業が混入している。
**コミット前に必ず `git branch --show-current` と `git diff --cached --stat` で確認すること。**

## main HEAD: `74f5fe6`

## ブランチ状態 (監視 #3)

| ブランチ | +N | 状態 | 備考 |
|---------|---|------|------|
| L3 | +0 | 未着手 | 作業は L7(54391c1) と L6(f82633e) に混入 |
| L4 | +2 | **完了** | acfd450 ErrorBoundary + a1778eb Users CRUD |
| L6 | +3 | 混入あり | 51df20c H-5修正(本来) + L7/L3混入2件 |
| L7 | +6 | 混入あり | 4af92c3,d9b0601,6896c08(本来) + L3/L6/L9混入3件 |
| L9 | +0 | 未着手 | 作業は L7(54391c1+52cd986) に混入 |

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
