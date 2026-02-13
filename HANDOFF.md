# 引き継ぎドキュメント — SOMS 全作業状態

**更新日**: 2026-02-13
**ブランチ**: main (未コミット変更あり)
**状態**: システム停止済み — ダッシュボード音声機能改善 + LLM切替完了

---

## 1. 今回のセッションの作業サマリ

### Session D (今回): ダッシュボード音声改善 + LLM切替

#### D-1. ダッシュボード音声バグ修正 (3件)

| 問題 | 原因 | 修正 |
|------|------|------|
| 受諾時音声が出ない | `handleAccept` が TODO スタブだった | VOICEVOX synthesize API 呼び出しを実装 |
| 完了時音声が出ない | nginx に voice API プロキシがなかった | `/api/voice/` → voice-service プロキシ追加 |
| 同じ音声が何度も再生される | バックエンド重複処理が DELETE→CREATE (新ID) だった | UPDATE in place (ID保持) に変更 |

#### D-2. タスク内容と音声の不一致修正

| 問題 | 原因 | 修正 |
|------|------|------|
| 「室温を下げてください」タスクに「コーヒー豆が空です」音声 | mock-LLM がプロンプト内の出力例 "コーヒー" にキーワードマッチしていた | mock-LLM に `tools` 有無で分岐するテキスト生成ハンドラを追加 |

#### D-3. リジェクション音声ストックシステム (新機能)

アイドル時にLLMで罵倒/嘆きテキストを生成し、VOICEVOXで音声合成してストック。
タスク無視時に即座に再生 (レイテンシゼロ)。

- ストック上限: 100件
- 補充閾値: 80件未満で自動生成開始
- アイドル検知: 全音声エンドポイントにビジー追跡
- 生成間隔: 3秒 (アイドル時)、30秒 (ストック充足時)
- フォールバック: ストック空時はオンデマンド生成

#### D-4. ダッシュボードUI改善

- タスクカード: 受諾→「対応中」バッジ+完了ボタン / 無視→非表示
- 優先度バッジ: `bounty_gold` ベースから `urgency` フィールド直接参照に変更
- 初回ロード時の自動再生スキップ (既存タスクは再生しない)
- 受諾済みタスクが上部にソート

#### D-5. LLM切替 (mock-llm → ローカル ollama)

- `.env`: `LLM_API_URL=http://host.docker.internal:11434/v1`
- `docker-compose.yml`: brain, voice-service に `extra_hosts: host.docker.internal:host-gateway` 追加
- ローカル ollama (qwen2.5:14b Q4_K_M) が `0.0.0.0:11434` でリッスン確認済み

#### D-6. 正常時の不要な発話を抑制

- `system_prompt.py`: speak の使用場面から「観察報告」を削除
- 「**正常時にspeakを使ってはいけない**」を明記

---

## 2. 過去セッションの作業 (コミット済み)

### Session A: Edge デバイスリファクタリング (Phase 1-5)
- per-channel テレメトリ `{"value": X}` 形式
- 共有ライブラリ `edge/lib/soms_mcp.py`、`config.json` サポート
- 診断スクリプト `edge/tools/` へ移動
- MCP JSON-RPC 2.0 対応 (C++ / MicroPython)

### Session B: バグ修正
- `models.py` 重複カラム削除
- `docker-compose.yml` voice-service LLM_API_URL

### Session C: カーネル安定化 + GPU 分離
- dGPU (RX 9700) のみ Docker にパススルー
- amdgpu-dkms ビルド成功
- GRUB デフォルトカーネル設定
- GPU分離検証スクリプト

---

## 3. 未コミットの変更一覧

### 変更ファイル (10 files, +414/-121)

```
 M infra/docker-compose.yml                     # extra_hosts (host.docker.internal)
 M infra/mock_llm/main.py                       # voice用テキスト生成ハンドラ追加
 M services/brain/src/system_prompt.py           # 正常時speak禁止
 M services/dashboard/backend/routers/tasks.py   # 重複タスクUPDATE in place
 M services/dashboard/frontend/nginx.conf        # /api/voice/ プロキシ追加
 M services/dashboard/frontend/src/App.tsx        # accept/ignore/complete音声、状態管理
 M services/dashboard/frontend/src/components/TaskCard.tsx  # urgency直接参照、受諾UI
 M services/perception/Dockerfile                # (前セッションからの変更)
 M services/voice/src/main.py                    # rejection API、ビジー追跡、lifespan
 M services/voice/src/speech_generator.py        # rejection テキスト生成
```

### 新規ファイル

```
?? infra/scripts/benchmark_llm.py               # (前セッション)
?? services/voice/src/rejection_stock.py         # リジェクション音声ストック管理
```

---

## 4. 推奨コミット分割

```bash
# コミット1: ダッシュボード音声バグ修正 + UI改善
git add services/dashboard/backend/routers/tasks.py \
      services/dashboard/frontend/nginx.conf \
      services/dashboard/frontend/src/App.tsx \
      services/dashboard/frontend/src/components/TaskCard.tsx
git commit -m "fix: dashboard voice playback — dedup, accept/complete/ignore audio, UI states"

# コミット2: リジェクション音声ストックシステム
git add services/voice/src/rejection_stock.py \
      services/voice/src/speech_generator.py \
      services/voice/src/main.py
git commit -m "add: rejection voice stock — idle-time LLM+VOICEVOX pre-generation (max 100)"

# コミット3: mock-LLM テキスト生成修正
git add infra/mock_llm/main.py
git commit -m "fix: mock-LLM voice text generation — separate handler for toolless requests"

# コミット4: LLM切替 + Brain発話制御
git add .env infra/docker-compose.yml services/brain/src/system_prompt.py
git commit -m "feat: switch to local ollama, suppress speak on normal status"
```

---

## 5. テスト結果

| テスト項目 | 結果 | 備考 |
|-----------|------|------|
| nginx voice API プロキシ | PASS | POST /api/voice/synthesize → 200, audio 6KB |
| 音声ファイル配信 | PASS | GET /audio/*.mp3 → 200 |
| 重複タスクID保持 | PASS | 同一title+location → 同一ID (id=6==6) |
| リジェクションストック生成 | PASS | 起動15秒で17件生成 |
| リジェクションランダム取得 | PASS | 「せっかく最適化してあげたのに……。」等 |
| ストッククリア+再生成 | PASS | clear → 0件 → 自動補充開始 |
| mock-LLM 音声テキスト (温度) | PASS | 「mainで室温を下げてください」(コーヒーではない) |
| mock-LLM 完了テキスト | PASS | 「室温を下げてくださいの対応、助かりました」 |
| mock-LLM リジェクション | PASS | 10パターンからランダム |
| mock-LLM Brain (tools付き) | PASS | tool_calls で create_task 返却 (従来通り) |
| ローカル ollama 接続 | 確認済み | qwen2.5:14b Q4_K_M, 0.0.0.0:11434 |

---

## 6. 次のアクション

### A. 起動手順

```bash
cd /home/sin/code/Office_as_AI_ToyBox

# 1. DB ボリューム削除 (スキーマ変更時のみ)
# sudo docker volume rm soms_db_data 2>/dev/null

# 2. 全サービス起動 (ollama はホスト上で稼働中)
sudo docker compose -f infra/docker-compose.yml \
  -f infra/docker-compose.edge-mock.yml \
  up -d --build \
  mosquitto backend frontend brain voice-service voicevox mock-llm virtual-edge
```

### B. 動作確認

```bash
# ダッシュボード
xdg-open http://localhost

# LAN内アクセス (スマホ等)
# http://192.168.128.74

# リジェクションストック状態
curl -s http://localhost:8002/api/voice/rejection/status

# Brain ログ (ollama 経由の推論を確認)
sudo docker logs -f soms-brain

# voice-service ログ (リジェクション生成を確認)
sudo docker logs -f soms-voice
```

### C. 本番移行チェックリスト

- [ ] ollama で qwen2.5:14b の推論が正常に動作することを確認
- [ ] Brain の ReAct サイクルで正常時に speak が呼ばれないことを確認
- [ ] リジェクションストックが ollama 経由で多様なテキストを生成することを確認
- [ ] LAN内端末からダッシュボードにアクセスし、受諾/完了/無視の音声を確認
- [ ] 長時間稼働テスト (ストック100件到達 + ローテーション)

---

## 7. 既知の問題

| 問題 | 重要度 | 詳細 |
|------|--------|------|
| User model/schema 不一致 | 低 | `models.py` は `credits`、`schemas.py` は `gold/xp/level` |
| DRI ノード番号変動リスク | 中 | カーネル変更で card1/card2 入れ替わる可能性 |
| 受諾音声は VOICEVOX 合成待ち | 低 | ストック化されていないため 1-2秒のレイテンシあり |
| perception/Dockerfile 変更 | 低 | 前セッションの残り、今回未テスト |

---

## 8. アーキテクチャ図 (音声フロー)

```
[Brain ReAct cycle]
  ├─ create_task → dashboard_client → voice announce_with_completion
  │   → LLM テキスト生成 → VOICEVOX 合成
  │   → announcement_audio_url + completion_audio_url をタスクに保存
  │
  └─ speak → voice synthesize → VOICEVOX 合成 → VoiceEvent DB

[Dashboard Frontend]
  ├─ 新タスク到着  → announcement_audio_url 自動再生
  ├─ [受諾] ボタン → POST /api/voice/synthesize (定型フレーズ) → 再生
  ├─ [完了] ボタン → completion_audio_url 再生 → PUT /api/tasks/{id}/complete
  └─ [無視] ボタン → GET /api/voice/rejection/random (ストックから即座) → 再生

[Voice Service - Background]
  └─ idle_generation_loop (30秒間隔)
      └─ stock < 80 && idle → LLM rejection text → VOICEVOX 合成 → stock 追加
```

---

## 9. ハードウェア構成

| コンポーネント | 詳細 |
|---------------|------|
| CPU | AMD Ryzen (Raphael, iGPU 内蔵) |
| dGPU | AMD RX 9700 XT (RDNA4, 32GB VRAM, PCI 03:00.0) |
| iGPU | AMD Raphael (PCI 0e:00.0, ディスプレイ用) |
| カーネル | 6.17.0-14-generic |
| amdgpu-dkms | 6.16.6-2255209.24.04 |
| LLM | qwen2.5:14b (Q4_K_M, ローカル ollama) |
| TTS | VOICEVOX (speaker 47: ナースロボ_タイプT) |
