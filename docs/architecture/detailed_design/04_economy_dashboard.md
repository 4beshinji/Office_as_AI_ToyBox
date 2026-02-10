# 04. Bio-Digital Economy & Dashboard

## 1. Concept: Human-in-the-Loop (HITL) as a Service
SOMS acknowledges that not all office tasks can be automated by robots. The Bio-Digital Economy bridges this "last mile" by incentivizing humans to perform physical actions (e.g., closing windows, refilling coffee beans) through a gamified credit system.

## 2. Infrastructure: The Dashboard
The Dashboard is the primary touchpoint for humans, serving as a marketplace for tasks and a wallet for earned credits.

### 2.1 Technology Stack
-   **Frontend**: React 18 (with TypeScript) + Tailwind CSS + Lucide React (Icons).
    -   *Why*: Responsive, component-based, and broadly supported ecosystem.
-   **Backend**: Python FastAPI.
    -   *Why*: High performance (ASYNC), seamless integration with the LLM Python Bridge, and automatic OpenAPI documentation.
-   **Real-time Communication**: WebSocket (Socket.IO).
    -   *Why*: Push notifications for new tasks (bounties) and instant balance updates.
-   **Database**: SQLite.
    -   *Why*: Zero-configuration, transactional integrity (ACID), and sufficient performance for office scale.

### 2.2 Core Features
-   **Task Feed**: List of available jobs with credit rewards.
    -   Cards display: `Title`, `Description`, `Reward Amount`, `Urgency Level`.
    -   Actions: `Accept`, `Complete`, `Ignore`.
-   **Wallet**: Shows current balance and transaction history.
-   **Notifications**: Browser-native push notifications for high-priority tasks.
-   **Leaderboard**: Optional gamification element (Weekly Top Earner).

## 3. Economic Model: The "Honor System"
### 3.1 Philosophy
We adopt a **Good Faith** model.
-   **No User Accounts**: The system does not track individuals (no login required).
-   **Instant Gratification**: The "Reward" is the immediate physical result (e.g., proper lighting) or a tangible item taken freely (e.g., "Take a snack from the box").
-   **Motivation**: Gamification is used only to signal *urgency* and *appreciation*, not to gatekeep resources.

### 3.2 Dynamic Pricing (Signaling)
The "Bounty" (OC) communicates priority.
-   **Low (5 OC)**: "Nice to have" (e.g., Straighten up chairs).
-   **High (100 OC)**: "Urgent/Safety" (e.g., Leak detected, Window open in storm).

## 4. Simplified Data Structure (SQLite)
We remove the complex Ledger and User tables.

```sql
-- Tasks Table (Ephemeral)
CREATE TABLE tasks (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    location TEXT, -- e.g., "Kitchen"
    bounty_amount INTEGER,
    status TEXT CHECK(status IN ('OPEN', 'COMPLETED', 'EXPIRED')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```
-   **No "Assigned User"**: Anyone can pick up a task.
-   **No "Wallet"**: Credits are not stored. They are "scores" for the day.

## 5. Anti-Gaming
Since there is no real-world value exchange (crypto/fiat), "gaming" the system (clicking complete without doing work) has no negative impact other than incorrect system state.
-   **Mitigation**: If a sensor detects the state hasn't changed (e.g., Temp still rising after "Window Closed" task), the System simply re-issues the task with a "Help Needed" flag.
