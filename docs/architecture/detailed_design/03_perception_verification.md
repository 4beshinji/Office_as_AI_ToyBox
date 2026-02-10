# 03. Perception & State Verification

## 1. Objective: From Pixels to Semantics
The Perception Layer transforms raw visual data (pixels) into structured information (JSON) that the LLM can reason about. It serves two critical functions:
1.  **State Monitoring**: Continuously observing the environment to detect anomalies (e.g., "Window left open during rain").
2.  **Visual Verification (Proof of Work)**: Validating that a human or robot has completed a requested task.

## 2. Technology Stack
-   **Model**: **YOLOv11** (Ultralytics).
    -   *Why*: State-of-the-art balance between speed and accuracy. The "Small" (v11s) or "Medium" (v11m) variants are suitable for the RTX 3090/4090 alongside the LLM.
-   **Hardware**: 
    -   Inference runs on the Central Server GPU.
    -   Image capture is performed by distributed ESP32-CAMs or Raspberry Pis streaming via RTSP.

## 3. Pre-trained Perception (No Fine-Tuning)
To minimize maintenance cost, we avoid custom training. We rely on **YOLOv11 Standard COCO Classes**:
-   `person`: For occupancy and "presence verification".
-   `cup`, `bottle`, `chair`: For general clutter estimation.

### 3.1 "Good Enough" State Inference
Instead of training a "Window Open" model:
-   **Contextual Guess**: If `person` is detected near the window zone AND temperature is dropping, we assume "Window Interaction" might be happening.
-   **Snapshot Logging**: When a task is completed, we just save a snapshot. We do not run an expensive ML verifier.

## 4. Visual Verification Strategy: "Trust + Audit"
### Workflow:
1.  **Task**: "Close Window".
2.  **Human Action**: Human closes window and clicks "Done".
3.  **System Action**:
    -   **Capture**: Take immediate Snapshot.
    -   **Store**: Save to `/var/logs/snapshots/{task_id}.jpg`.
    -   **Resolve**: Mark task as `COMPLETED` immediately.
4.  **Audit**: If the temperature doesn't stabilize, the LLM can review the snapshot *later* (using a Vision-Language Model capability) or a human admin can check it.

## 5. Privacy (Ephemeral Processing)
-   **RAM-Only**: Video streams are processed in RAM.
-   **Retention**: 
    -   Stream: Discarded instantly.
    -   Task Snapshots: Kept for 24h then auto-deleted.
-   **Blurring**: Applied immediately to `face` regions in snapshots.
