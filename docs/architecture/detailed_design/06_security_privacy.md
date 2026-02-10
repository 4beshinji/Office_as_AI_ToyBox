# 06. Security, Privacy & Safety

## 1. Safety Philosophy: "Trust but Verify"
An autonomous system controlling physical infrastructure must be designed with the assumption that the AI *will* make mistakes (hallucinate) or be compromised. Therefore, safety is not an afterthought but a foundational layer.

## 2. Preventing AI Hallucinations
LLMs can generate plausible but incorrect instructions (e.g., commanding a heater to 500°C).

### 2.1 Schema Validation
As detailed in Doc 01, we use JSON Schemas to constrain output syntax.

### 2.2 Semantic Sanitation (The "Logic Gate")
A dedicated Python module (`Sanitizer`) intercepts every tool call before it reaches the MQTT bus.
-   **Range Checks**:
    -   `set_temperature(val)`: valid range `[18, 28]`.
    -   `run_pump(duration)`: max `60s`.
-   **Device Existence**: Verify `device_id` against a hardcoded `inventory.yaml`.
    -   If LLM calls `turn_on(light_99)` and `light_99` does not exist -> **REJECT**.
-   **State Consistency**:
    -   If `window.state == 'open'`, reject `turn_on_ac`.

## 3. Physical & Hardware Safety (Cost-Effective)
Since most automated systems (lights, fans, small pumps) are not mission-critical, we prioritize software safety over expensive hardware interlocks.

### 3.1 Software Limits ("The fuse")
-   **Rate Limiting**: Actuators have software-imposed limits (e.g., "Pump on for max 10s").
-   **Sanity Checks**: The `Sanitizer` module rejects outliers (e.g., Target Temp > 35°C).

### 3.2 Minimal Hardware Stops
-   **Water**: The only critical hardware safety is a physical **Float Switch** that cuts power to the pump if the tank is empty (preventing burnout) or full (preventing overflow).
-   **Thermal**: Standard thermal fuses built into heaters are sufficient; no extra external circuitry required.

## 4. Privacy & Data Protection
Cameras in the office are sensitive.

### 4.1 Edge Computing Privacy
-   **No Cloud Uploads**: All video processing happens on the Local Server (RTX 3090). No images leave the premises.
-   **Retention Policy**: 
    -   Raw Video: Metrics only (occupancy count), video discarded instantly.
    -   Verification Images: Stored for 7 days (for dispute resolution), then deleted.
-   **Face Anonymization**: 
    -   The `YOLO` process detects `face` class.
    -   A post-processing step applies Gaussian Blur to the bounding box *before* saving any image.

## 5. Network Security
### 5.1 Isolation
-   **VLAN**: IoT devices live on a separate VLAN (`SOMS_IoT`) with no internet access.
-   **Firewall**: The Central Server allows strict inbound connections:
    -   MQTT (1883) from IoT VLAN.
    -   Dashboard (80/443) from Office LAN.
    -   SSH (22) from Admin IP only.

### 5.2 Authentication
-   **MQTT**: Strong passwords for every ESP32 client.
-   **Dashboard**: OAuth2 (Google/Microsoft) or internal SSO for human users.
-   **Role-Based Access Control (RBAC)**:
    -   `User`: View tasks, Claim bounties.
    -   `Admin`: Override system, View logs, Adjust budget.
