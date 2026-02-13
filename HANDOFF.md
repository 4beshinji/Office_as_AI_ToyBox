# 引き継ぎドキュメント — SOMS 全作業状態

**更新日**: 2026-02-13
**ブランチ**: main (未コミット変更あり)
**状態**: 再起動前 — カーネル安定化 + GPU 分離完了、Docker 起動未実施

---

## 1. 今回の作業サマリ (3 セッション分)

### Session A: Edge デバイスリファクタリング (Phase 1-5)

- Secondary IP `192.168.128.161/24` を `wlp11s0` に追加 (NetworkManager 永続化、connection: `"GITY Wi-Fi"`)
- sensor-02 テレメトリを per-channel `{"value": X}` 形式に変更
- 共有ライブラリ `edge/lib/soms_mcp.py` 作成、`config.json` サポート
- 17 個の診断スクリプトを `edge/tools/` に移動、`mcp_device.py` 削除
- C++ sensor-node / camera-node を MCP JSON-RPC 2.0 対応
- Virtual edge を WorldModel 互換に更新

### Session B: バグ修正 2 件

| 修正 | ファイル | 内容 |
|------|---------|------|
| Task モデル重複カラム [致命的] | `services/dashboard/backend/models.py` | `announcement_audio_url` 等が 2 回定義 → SQLAlchemy 起動不能 → 2 回目を削除 |
| Voice Service LLM URL [致命的 in dev] | `infra/docker-compose.yml:86` | `LLM_API_URL` ハードコード → `${LLM_API_URL:-http://mock-llm:8000/v1}` に変更 |

### Session C (今回): カーネル安定化 + GPU 分離

**背景**: `docker run ... --device /dev/dri ollama/ollama:rocm` で iGPU もコンテナに公開 → GNOME Wayland クラッシュ → 物理リブート強要

| GPU | PCI | DRI | VRAM | 用途 |
|-----|-----|-----|------|------|
| RX 9700 (RDNA4) | 03:00.0 | card1 / renderD128 | 32 GB | ROCm コンピュート |
| Raphael iGPU | 0e:00.0 | card2 / renderD129 | 512 MB | ディスプレイ (GNOME) |

完了した作業:

1. **GPU 分離** (docker-compose 3 ファイル修正)
   - `/dev/dri` 全体 → `card1` + `renderD128` のみパススルー
   - 対象: `infra/docker-compose.yml` (ollama, perception), `infra/llm/docker-compose.yml` (llm-engine)

2. **GRUB 安全化** (ユーザー手動実施)
   - `GRUB_TIMEOUT_STYLE=menu`, `GRUB_TIMEOUT=5`
   - カーネル選択メニューが起動時に表示されるようになった

3. **amdgpu-dkms ビルド** — 成功
   - `amdgpu/6.16.6-2255209.24.04` を `6.8.0-41-generic` 向けにビルド・インストール完了
   - 8 モジュール: amdgpu, amdttm, amdkcl, amd-sched, amddrm_ttm_helper, amddrm_buddy, amddrm_exec, amdxcp
   - `/lib/modules/6.8.0-41-generic/updates/dkms/` にインストール済み

4. **デフォルトカーネル設定** (ユーザー手動実施)
   - `grub-set-default` で `6.8.0-41-generic` をデフォルトに

5. **検証スクリプト作成**
   - `infra/scripts/verify_gpu_isolation.sh` — 8 項目の自動検証

---

## 2. 未コミットの変更一覧

### 変更ファイル (10 files, +509/-320)

```
 M CLAUDE.md                                  # プロジェクト説明更新
 M edge/office/sensor-02/main.py              # per-channel telemetry
 D edge/office/sensor-02/mcp_device.py        # 削除 (soms_mcp.py に統合)
 M edge/office/sensor-node/main.py            # per-channel telemetry + config.json
 M edge/test-edge/camera-node/src/main.cpp    # MCP call_tool 対応
 M edge/test-edge/sensor-node/src/main.cpp    # MCP call_tool + per-channel
 R edge/office/sensor-02/*.py -> edge/tools/  # 17個の診断スクリプト移動
 M infra/docker-compose.yml                   # voice-service LLM_API_URL + GPU分離
 M infra/llm/docker-compose.yml               # GPU分離 (card1/renderD128のみ)
 M infra/virtual_edge/src/device.py           # get_status tool 追加
 M infra/virtual_edge/src/main.py             # topic prefix 更新
 M services/dashboard/backend/models.py       # 重複カラム削除
```

### 新規ファイル (untracked)

```
?? HANDOFF.md                                 # 本ドキュメント
?? docs/CITY_SCALE_VISION.md                  # 将来構想ドキュメント
?? docs/SYSTEM_OVERVIEW.md                    # システム概要ドキュメント
?? edge/office/sensor-02/config.json          # MicroPython 設定
?? edge/office/sensor-node/config.json        # MicroPython 設定
?? infra/scripts/verify_gpu_isolation.sh      # GPU分離検証スクリプト
```

---

## 3. 次のアクション (優先順)

### A. 再起動 + 検証 (今すぐ)

```bash
# 1. GRUB_DEFAULT=saved が設定済みか確認
grep GRUB_DEFAULT /etc/default/grub
# → "saved" でなければ修正して sudo update-grub

# 2. 再起動
sudo reboot

# 3. 検証スクリプト実行
cd /home/sin/code/Office_as_AI_ToyBox
sudo bash infra/scripts/verify_gpu_isolation.sh
```

**検証スクリプトの項目**:
1. カーネルバージョン (6.8.0-41-generic 期待)
2. amdgpu モジュールのロード
3. DRI デバイス存在 (card1/card2/renderD128/renderD129)
4. by-path マッピング — dGPU が card1/renderD128 か確認
5. ホスト rocm-smi
6. Docker コンテナ内 rocm-smi (dGPU のみ見えること)
7. GRUB 設定
8. docker-compose デバイス設定

**DRI ノード番号が入れ替わっていた場合**: スクリプトが `[FAIL]` で警告を出す。`infra/docker-compose.yml` と `infra/llm/docker-compose.yml` の card/renderD 番号を実際の dGPU デバイスに合わせて修正すること。

### B. コミット (検証後)

推奨コミット分割:

```bash
# コミット1: Edge リファクタリング (Phase 1-5)
git add edge/ CLAUDE.md
git commit -m "refactor: edge devices — per-channel telemetry, MCP JSON-RPC 2.0, shared lib"

# コミット2: バグ修正
git add services/dashboard/backend/models.py
git commit -m "fix: remove duplicate voice announcement columns in Task model"

# コミット3: GPU分離 + インフラ
git add infra/
git commit -m "fix: GPU isolation — passthrough dGPU only, add verification script"

# コミット4: ドキュメント
git add HANDOFF.md docs/
git commit -m "docs: add handoff document and system overview"
```

### C. Docker 起動と動作確認

```bash
# 1. 古い DB ボリューム削除 (スキーマ変更のため必須)
sudo docker volume rm soms_db_data 2>/dev/null

# 2. サービス起動 (GPU 不要なもののみ)
cd /home/sin/code/Office_as_AI_ToyBox/infra
sudo docker compose --env-file ../.env \
  -f docker-compose.yml -f docker-compose.edge-mock.yml \
  up --build -d \
  mosquitto backend frontend brain voice-service voicevox mock-llm virtual-edge

# ※ perception と ollama は GPU (ROCm) 必須 — 検証後に別途起動
```

### D. 動作確認チェックリスト

```bash
# 全コンテナが Running か確認
sudo docker ps

# Backend: SQLAlchemy エラーがないこと
sudo docker logs soms-backend 2>&1 | head -30

# Brain: ReAct サイクルが動作していること
sudo docker logs soms-brain 2>&1 | head -30

# Voice: VOICEVOX 接続が正常なこと
sudo docker logs soms-voice 2>&1 | head -30

# API テスト
curl -s http://localhost:8000/tasks/ | python3 -m json.tool
curl -s http://localhost:8000/docs > /dev/null && echo "Swagger UI OK"

# ダッシュボード
xdg-open http://localhost
```

期待される動作フロー:
```
virtual-edge → MQTT (温度/CO2/湿度) → brain (WorldModel → ReAct) → mock-llm
  → create_task → backend → dashboard
  → speak → voice-service → voicevox → 音声合成
```

---

## 4. 既知の問題

| 問題 | 重要度 | 詳細 |
|------|--------|------|
| User model/schema 不一致 | 低 | `models.py` は `credits`、`schemas.py` は `gold/xp/level`。users router はスタブのため非ブロッカー |
| カーネル 6.17 不安定 | 中 | HWE 開発版。6.8 切り替え後は解消される想定 |
| DRI ノード番号変動リスク | 中 | カーネル変更で card1/card2 入れ替わる可能性。検証スクリプトで検出可能 |

---

## 5. ハードウェア構成

| コンポーネント | 詳細 |
|---------------|------|
| CPU | AMD Ryzen (Raphael, iGPU 内蔵) |
| dGPU | AMD RX 9700 XT (RDNA4, 32GB VRAM, PCI 03:00.0) |
| iGPU | AMD Raphael (PCI 0e:00.0, ディスプレイ用) |
| カーネル (現在) | 6.17.0-14-generic (HWE 開発版) |
| カーネル (目標) | 6.8.0-41-generic (Ubuntu 24.04 GA 安定版) |
| amdgpu-dkms | 6.16.6-2255209.24.04 (両カーネル向けビルド済み) |
| Wi-Fi | wlp11s0, secondary IP: 192.168.128.161/24 (Edge デバイス通信用) |

---

## 6. サービスポート一覧

| サービス | ポート | コンテナ名 |
|---------|--------|-----------|
| Dashboard Frontend | 80 | soms-frontend |
| Dashboard Backend API | 8000 | soms-backend |
| Mock LLM | 8001 | soms-mock-llm |
| Voice Service | 8002 | soms-voice |
| VOICEVOX Engine | 50021 | soms-voicevox |
| Ollama (LLM) | 11434 | soms-ollama |
| MQTT | 1883 | soms-mqtt |

## 7. MQTT トピック規約

```
office/{zone}/sensor/{device_id}/{channel}  → {"value": X}
mcp/{device_id}/request/call_tool           → JSON-RPC 2.0
mcp/{device_id}/response/{request_id}       → JSON-RPC 2.0
{topic_prefix}/heartbeat                    → 60秒間隔
```
