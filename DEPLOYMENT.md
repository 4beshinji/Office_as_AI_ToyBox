# SOMS デプロイメントガイド (Deployment Guide JA)

## 1. 前提条件 (本番運用環境)
ターゲットマシンに以下がインストールされていることを確認してください。
-   **OS**: Linux (Ubuntu 22.04+ 推奨)
-   **Git**: `sudo apt install git`
-   **Docker Engine**: [インストールガイド](https://docs.docker.com/engine/install/ubuntu/)
-   **Docker Compose**: `sudo apt install docker-compose-plugin`
-   **AMD Drivers (ROCm)**: ローカルLLMを使用する場合にのみ必要です。[インストールガイド](https://rocm.docs.amd.com/en/latest/deploy/linux/quick_start.html)。
    -   `rocminfo` または `clinfo` コマンドで動作を確認してください。

## 2. クローンとセットアップ
1.  **リポジトリの複製**:
    ```bash
    git clone <repository_url> bigbrother
    cd bigbrother
    ```
2.  **環境設定**:
    ```bash
    cp env.example .env
    # 設定を変更する場合は .env を編集してください (例: 実際のLLMを使用する場合など)
    nano .env
    ```
3.  **初期化 (ボリュームとネットワーク作成)**:
    ```bash
    chmod +x infra/scripts/setup_dev.sh
    ./infra/scripts/setup_dev.sh
    ```

## 3. 利用シナリオの実行

### シナリオ A: 完全シミュレーション (ハードウェア不要・GPU不要)
ロジックやネットワークフローの検証に最適です。
```bash
# Brain, Dashboard, Mock LLM, Virtual Camera, Virtual Edge を起動します
./infra/scripts/start_virtual_edge.sh
```
-   **検証方法**: `python3 infra/scripts/integration_test_mock.py` を実行して、テストイベントをトリガーしてください。

### シナリオ B: 実機本番環境 (GPU + エッジデバイス)
1.  **`.env` の編集**:
    -   `LLM_API_URL=http://llm-engine:8000/v1` を設定。
    -   `RTSP_URL` を実際のカメラのIPアドレスに設定。
2.  **`infra/docker-compose.yml` の編集**:
    -   `llm-engine` サービスブロックのコメントアウトを外す。
    -   GPUに合わせた `devices` マッピング (`/dev/kfd` 等) が正しいか確認。
3.  **システムの起動**:
    ```bash
    docker-compose -f infra/docker-compose.yml up -d --build
    ```

## 4. トラブルシューティング
-   **MQTT Connection Refused**: `mosquitto` コンテナが起動しているか確認してください (`docker ps`)。
-   **LLM Out of Memory**: `rocm-smi` でVRAM使用量を確認してください。`docker-compose.yml` 内の `gpu-memory-utilization` 値を下げてみてください。
-   **Permission Denied**: ユーザーが `docker` および `video`/`render` グループに追加されているか確認してください。
