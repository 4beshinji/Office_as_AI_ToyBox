# 引き継ぎドキュメント — SOMS 全作業状態

**更新日**: 2026-02-13
**ブランチ**: main
**最新コミット**: `1413511 temp:quota` (全変更コミット済み)
**状態**: ローカル LLM (ollama) テスト完了・ベンチマーク実施済み

---

## 1. 今回のセッションの作業サマリ

### Session E (今回): GPU テスト + ローカル LLM ベンチマーク

#### E-1. GPU / ROCm 検証

| 項目 | 結果 |
|------|------|
| カーネル | 6.17.0-14-generic (amdgpu-dkms 6.16.6 ロード済み) |
| dGPU 認識 | gfx1201 — AMD Radeon AI PRO R9700 (RX 9700) |
| iGPU 認識 | gfx1036 — AMD Radeon Graphics (Raphael) |
| DRI デバイス | card1/renderD128 (dGPU), card2/renderD129 (iGPU) |
| ROCm | 6.16.6 正常動作 |
| GPU 分離 | Docker に card1+renderD128 のみパススルー → iGPU 安全 |

#### E-2. Ollama コンテナ起動

- `ollama/ollama:rocm` イメージ使用
- `HSA_OVERRIDE_GFX_VERSION=12.0.1` で RDNA4 互換性確保
- VRAM 31.9 GiB 認識 (デフォルトコンテキスト 32768 トークン)
- qwen2.5:14b モデル pull 完了 (9.0 GB)

#### E-3. Brain → Ollama 接続検証

- `.env` を `http://host.docker.internal:11434/v1` に切替
- `LLM_MODEL=qwen2.5:14b` を追加
- docker-compose に `--env-file .env` 指定が必要 (`infra/` ディレクトリがプロジェクトルートになるため)
- Brain ReAct サイクルで正常応答確認: 「現在のmainゾーンは快適な温度と湿度を保っています。異常はありません。」

#### E-4. Perception Dockerfile 修正

- `libgl1-mesa-glx` → `libgl1` に変更 (`rocm/pytorch:latest` ベースイメージで廃止されたため)

#### E-5. LLM ベンチマーク実施

`infra/scripts/benchmark_llm.py` を作成・実行 (標準ライブラリのみ、外部依存なし)

---

## 2. ベンチマーク結果 — RX 9700 + qwen2.5:14b

### シナリオ別パフォーマンス

| シナリオ | レイテンシ | 速度 | 応答種別 | 判断の正確性 |
|----------|-----------|------|----------|-------------|
| 正常データ (23.5℃) | 3,328 ms | 49.0 tok/s | テキスト | 正しく「異常なし」 |
| 高温異常 (32.8℃) | 6,595 ms | 52.3 tok/s | speak + create_task | 適切にツール選択 |
| CO2 超過 (1450ppm) | 3,709 ms | 51.8 tok/s | テキスト | CO2超過を認識 |
| 単純挨拶 (ツールなし) | 2,011 ms | 51.7 tok/s | テキスト | 最速応答 |

### シーケンシャルスループット (5回連続)

| 指標 | 値 |
|------|-----|
| 平均レイテンシ | 4,537 ms |
| P50 レイテンシ | 3,986 ms |
| 平均速度 | 51.6 tok/s |

### 同時3リクエスト

| 指標 | 値 |
|------|-----|
| ウォールタイム | 15,121 ms |
| 最大個別レイテンシ | 15,120 ms |
| 集計スループット | 89.4 tok/s |

### 評価

- **単体性能**: ~50 tok/s で安定。Brain の 30秒サイクルに対して 3-7秒で応答 → 十分実用的
- **ツール呼び出し精度**: 高温シナリオで `speak` + `create_task` を適切に選択
- **並行性能**: Ollama はシングルキュー処理のため同時リクエストは直列化。Brain は単一プロセスなので問題なし
- **エラー**: 0件 / 12リクエスト

---

## 3. 過去セッションの作業

### Session D: ダッシュボード音声改善 + LLM切替

- ダッシュボード音声バグ修正 (受諾/完了/重複ID)
- リジェクション音声ストックシステム (`rejection_stock.py`)
- mock-LLM テキスト生成ハンドラ追加 (tools有無分岐)
- UI改善 (受諾/対応中/完了ステート遷移)
- 正常時の不要発話抑制 (`system_prompt.py`)

### Session C: カーネル安定化 + GPU 分離

- dGPU (RX 9700) のみ Docker にパススルー (`card1`+`renderD128`)
- amdgpu-dkms ビルド成功
- GRUB デフォルトカーネル設定
- GPU分離検証スクリプト (`infra/scripts/verify_gpu_isolation.sh`)

### Session B: バグ修正

- `models.py` 重複カラム削除
- `docker-compose.yml` voice-service LLM_API_URL

### Session A: Edge デバイスリファクタリング

- per-channel テレメトリ `{"value": X}` 形式
- 共有ライブラリ `edge/lib/soms_mcp.py`
- MCP JSON-RPC 2.0 対応

---

## 4. コミット履歴

```
1413511 temp:quota                     ← 今回セッションの全変更
9225b15 docs: add handoff document, system overview, and city-scale vision
faa711c fix: GPU isolation and infra improvements
e376f2f fix: remove duplicate voice announcement columns in Task model
ac6db35 refactor: edge devices — per-channel telemetry, MCP JSON-RPC 2.0, shared lib
009e5b5 add: 音声インタラクション機能 - speakツールによる直接対話モダリティ
```

### 推奨: temp:quota のコミットを分割する場合

```bash
# リセットして分割コミット
git reset --soft HEAD~1

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

# コミット4: LLM切替 + Brain発話制御 + インフラ
git add infra/docker-compose.yml services/brain/src/system_prompt.py \
      services/perception/Dockerfile
git commit -m "feat: switch to local ollama, suppress speak on normal status, fix perception Dockerfile"

# コミット5: ベンチマークツール + 引き継ぎ資料
git add infra/scripts/benchmark_llm.py HANDOFF.md
git commit -m "add: LLM benchmark tool and updated handoff document"
```

---

## 5. 現在の環境設定

### .env (重要な値)

```
LLM_API_URL=http://host.docker.internal:11434/v1
LLM_MODEL=qwen2.5:14b
MQTT_BROKER=mosquitto
DATABASE_URL=sqlite:///data/soms.db
```

### Docker 起動コマンド

```bash
# docker-compose 起動時に --env-file が必要
sudo docker compose -f infra/docker-compose.yml --env-file .env up -d

# ollama 単体起動
sudo docker compose -f infra/docker-compose.yml --env-file .env up -d ollama

# サービス再起動 (環境変数反映)
sudo docker compose -f infra/docker-compose.yml --env-file .env up -d --force-recreate brain voice-service
```

**注意**: `-f infra/docker-compose.yml` 指定時、docker-compose はプロジェクトディレクトリを `infra/` とみなすため、ルートの `.env` は `--env-file .env` で明示的に指定する必要がある。

---

## 6. テスト結果

### Session E (GPU + LLM)

| テスト項目 | 結果 | 備考 |
|-----------|------|------|
| GPU 認識 (gfx1201 / RX 9700) | PASS | ROCm 6.16.6 |
| VRAM 31.9 GiB | PASS | デフォルト ctx 32768 |
| Ollama コンテナ起動 | PASS | v0.16.0 |
| qwen2.5:14b モデルロード | PASS | 9.0 GB |
| Brain → Ollama 通信 | PASS | ReAct サイクル正常 |
| LLM ベンチマーク (12リクエスト) | PASS | 0エラー、avg 51.6 tok/s |
| ツール呼び出し精度 | PASS | 高温で speak+create_task |
| GPU 分離 (card1/renderD128 のみ) | PASS | iGPU 無事 |
| perception Dockerfile | 修正済み | libgl1-mesa-glx → libgl1 (未テスト) |

### Session D (音声)

| テスト項目 | 結果 | 備考 |
|-----------|------|------|
| nginx voice API プロキシ | PASS | POST /api/voice/synthesize → 200 |
| 重複タスクID保持 | PASS | UPDATE in place |
| リジェクションストック生成 | PASS | 起動15秒で17件 |
| リジェクションランダム取得 | PASS | ストックから即座 |
| mock-LLM 音声テキスト | PASS | 内容一致 (コーヒー問題解消) |
| mock-LLM Brain (tools付き) | PASS | tool_calls 返却 |

---

## 7. 次のアクション

### A. 優先度高

1. **コミット分割** (任意): `temp:quota` を論理単位に分割
2. **perception リビルド・テスト**: Dockerfile 修正済み、動作未確認
   ```bash
   sudo docker compose -f infra/docker-compose.yml --env-file .env up -d --build perception
   ```
3. **全サービス統合テスト**: brain + ollama + voice + dashboard の E2E

### B. 優先度中

4. **ツール呼び出しテスト**: MQTT でセンサー異常値を送り込み、brain がタスク作成・speak を実行するか検証
5. **リジェクションストック (ollama版)**: mock-LLM ではなく ollama でストック生成を確認
6. **長時間稼働テスト**: ストック100件到達 + ローテーション

### C. 優先度低

7. User model/schema 不一致修正 (`credits` vs `gold/xp/level`)
8. 受諾音声のストック化 (現在は毎回 VOICEVOX 合成待ち 1-2秒)
9. DRI ノード番号変動対策 (udev ルール等)

---

## 8. アーキテクチャ図

### 音声フロー

```
[Brain ReAct cycle (30秒間隔)]
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

### LLM 接続トポロジ

```
[ホスト]
  ollama (0.0.0.0:11434) ← qwen2.5:14b (GPU: RX 9700)
     ↑
[Docker soms-net]
  brain         → http://host.docker.internal:11434/v1 (推論)
  voice-service → http://host.docker.internal:11434/v1 (テキスト生成)
  mock-llm      → 8001 (フォールバック / テスト用)
```

---

## 9. ハードウェア構成

| コンポーネント | 詳細 |
|---------------|------|
| CPU | AMD Ryzen 7 9800X3D (8C/16T, Raphael, iGPU 内蔵) |
| dGPU | AMD RX 9700 (RDNA4, gfx1201, 32GB VRAM, PCI 03:00.0) |
| iGPU | AMD Raphael (gfx1036, PCI 0e:00.0, ディスプレイ用) |
| カーネル | 6.17.0-14-generic |
| amdgpu-dkms | 6.16.6 (ROCk module) |
| Ollama | v0.16.0 (rocm イメージ) |
| LLM | qwen2.5:14b (9.0 GB, ~51 tok/s) |
| TTS | VOICEVOX (speaker 47: ナースロボ_タイプT) |

---

## 10. 既知の問題

| 問題 | 重要度 | 詳細 |
|------|--------|------|
| User model/schema 不一致 | 低 | `models.py` は `credits`、`schemas.py` は `gold/xp/level` |
| DRI ノード番号変動リスク | 中 | カーネル変更で card1/card2 入れ替わる可能性。`verify_gpu_isolation.sh` で検出可 |
| 受諾音声は合成待ち | 低 | ストック化されていないため 1-2秒レイテンシ |
| perception 未テスト | 中 | Dockerfile 修正済み (libgl1) だがリビルド・動作未確認 |
| CO2 シナリオでツール未使用 | 低 | ベンチマークで 1450ppm に対してテキスト応答のみ (ツール呼び出しなし) |
