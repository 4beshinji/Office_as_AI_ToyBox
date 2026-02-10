# 01. Central Intelligence & LLM Strategy

## 1. Overview
The **Central Intelligence Layer** acts as the "brain" of the Symbiotic Office Management System (SOMS). Unlike traditional rule-based Building Management Systems (BMS), SOMS utilizes a Large Language Model (LLM) to perform context-aware decision-making, natural language processing, and complex task planning. This document details the hardware infrastructure, model selection, optimization strategies, and the cognitive architecture required to instantiate this intelligence.

## 2. Infrastructure & Hardware
### 2.1 Server Specifications
- **GPU**: AMD Radeon Pro W7800 / W6800 (32GB VRAM) or high-end Consumer Radeon with 32GB+ VRAM (if available).
  - *Constraint*: The system is designed to run locally. We leverage the open-source **ROCm** stack which has matured significantly for LLM inference.
- **VRAM Requirement**: Minimum 32GB to comfortably host the 32B model with context.
- **CPU**: Modern Multi-core CPU (e.g., AMD Ryzen 9 or Intel Core i9) to handle preprocessing and the Python event loop.
- **RAM**: 64GB+ system RAM to support model loading and OS operations.
- **Storage**: NVMe SSD for fast model loading and log persistence.

### 2.2 Distributed Topology & Future Expansion
While currently designed for a single GPU node, the system uses **MQTT** to ensure loose coupling.
-   **Logical Center**: The "Central Intelligence" is a role, not a specific machine.
-   **Multi-Node Ready**: Future expansion can split the workload:
    -   **Node A (Intelligence)**: Runs LLM (Qwen2.5).
    -   **Node B (Vision)**: Runs YOLOv11 and stores video buffers.
    -   **Node C (Database/Web)**: Runs the Dashboard and Historical Data.
-   **Network**: Nodes communicate strictly over TCP/IP (MQTT/HTTP), allowing them to be physically separated across the office or even VPN.

## 3. Model Architecture
### 3.1 Model Selection: Qwen2.5-32B
We have selected **Qwen2.5-32B** (or its instructed variants) as the core model for the following reasons:
- **Instruction Following**: It demonstrates superior performance in adhering to complex instructions, particularly in generating structured output (JSON).
- **Coding & Logic**: High capabilities in code understanding and logical reasoning, essential for debugging system behavior and generating valid tool calls.
- **Multilingual Support**: Strong performance in multiple languages, making it suitable for diverse office environments.
- **Context Window**: Supports up to 128k context, allowing the system to verify historical data and long-term trends.
- **Efficiency**: The 32B size offers a "Goldilocks" balance—smart enough for complex reasoning but small enough to run on local hardware with quantization.

### 3.2 Optimization Strategy (32GB VRAM Target)
Running a 32B parameter model typically requires >60GB VRAM at FP16. To fit within 32GB, we employ the following:
- **Quantization**: 
  - **4-bit Quantization (AWQ/GPTQ/GGUF)**: vLLM supports ROCm, but checking compatibility with widely available `AWQ` models is crucial. If vLLM on ROCm proves unstable for specific quantizations, we can fallback to `llama.cpp` (GGUF) which has excellent AMD optimization.
  - **Performance Impact**: Negligible degradation for 32B models.
- **Inference Engine**: **vLLM (ROCm Backend)**
  - **PagedAttention**: Supported on ROCm, providing high throughput.
  - **Alternative**: `llama.cpp` server if vLLM ROCm configuration faces driver version mismatches.

## 4. Cognitive Architecture
### 4.1 Constitutional AI & System Prompt
To ensure the LLM behaves as a responsible "Office Manager" and not just a chatbot, we define a strict **System Prompt** based on Constitutional AI principles.

#### Key Components of the System Prompt:
1.  **Role Definition**: 
    > "You are the Autonomous Office Manager (AOM). Your mission is to optimize office comfort, energy efficiency, and human well-being."
2.  **Constraints (The Constitution)**:
    - **Budget Awareness**: "You possess a finite amount of 'Office Credits'. Do not waste them on trivial tasks."
    - **Safety First**: "Never execute actions that could harm humans or equipment. If unsure, ask for human confirmation."
    - **Privacy**: "Do not record or describe specific individuals' personal activities unrelated to office management."
3.  **Action Primitive (ReAct)**:
    - The model must output a `thought` process before every `action` (tool call).
    - Format: `Thought: [Analysis] -> Action: [Tool]`

### 4.2 Structured Output (JSON Enforcing)
To prevent runtime errors in the Python control layer, the LLM's output must be strictly structured.
- **Technology**: `outlines` library or vLLM's `guided_decoding`.
- **Mechanism**: The inference engine forces the output tokens to match a pre-defined JSON Schema (Pydantic model).
- **Benefit**: guarantees 100% syntactically correct JSON for downstream parsing.

#### Example Schema Structure:
```json
{
  "thought": "The temperature is 28C, which is above the target of 24C. The window sensor indicates it is open. I should ask a human to close it because I cannot control it directly.",
  "plan": [
    "Check window status (verified)",
    "Create task for human"
  ],
  "tool_calls": [
    {
      "name": "post_human_task",
      "args": {
        "title": "Close the meeting room window",
        "description": "Temperature is rising and AC is inefficient.",
        "bounty": 20,
        "priority": "medium"
      }
    }
  ]
}
```

## 5. Implementation Roadmap
1.  **Environment Setup**: Install AMD GPU Drivers, ROCm 6.x (or latest stable), and vLLM (ROCm build).
2.  **Model Acquisition**: Download `Qwen/Qwen2.5-32B-Instruct-AWQ` (or GPTQ/GGUF equivalent compatible with ROCm).
3.  **Server Development**:
    - Build a Python wrapper around the vLLM `AsyncLLMEngine`.
    - Implement the `generate(prompt, schema)` function.
4.  **Prompt Engineering**: Iteratively refine the System Prompt using evaluation datasets (e.g., simulated office scenarios).
