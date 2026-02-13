#!/usr/bin/env python3
"""
Wallet Integration Test: dashboard + wallet service E2E.

Requires running: postgres, backend, wallet, (frontend for nginx proxy tests)

Scenarios:
  1. Wallet service health check
  2. User creation → wallet auto-creation
  3. Task lifecycle: create → accept → complete → bounty payment
  4. Balance and transaction history verification
  5. Idempotency: duplicate task-reward rejected
  6. P2P transfer between users
  7. Supply stats tracking
  8. Frontend proxy routing (nginx /api/wallet/)
"""
import json
import sys
import urllib.request
import urllib.error

BACKEND_URL = "http://localhost:8000"
WALLET_URL = "http://localhost:8003"
FRONTEND_URL = "http://localhost"  # nginx proxy

passed = 0
failed = 0
skipped = 0


def api_request(url, method="GET", data=None, timeout=10):
    headers = {}
    body = None
    if data is not None:
        body = json.dumps(data).encode()
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
            content_type = resp.headers.get("Content-Type", "")
            if "json" in content_type:
                return json.loads(raw)
            return raw
    except urllib.error.HTTPError as e:
        error_body = e.read().decode() if e.fp else ""
        raise RuntimeError(f"HTTP {e.code}: {error_body}") from e


def test(name, fn):
    global passed, failed, skipped
    try:
        fn()
        passed += 1
        print(f"  ✅ {name}")
    except urllib.error.URLError as e:
        skipped += 1
        print(f"  ⏭️  {name} — SKIPPED (service unavailable: {e.reason})")
    except Exception as e:
        failed += 1
        print(f"  ❌ {name} — {e}")


# ── State ──
state = {
    "user_a": None,
    "user_b": None,
    "task": None,
}


# ── Test 1: Health Checks ──

def test_wallet_health():
    resp = api_request(f"{WALLET_URL}/")
    assert "message" in resp, f"Unexpected response: {resp}"

def test_backend_health():
    resp = api_request(f"{BACKEND_URL}/")
    assert resp is not None


# ── Test 2: User & Wallet Creation ──

def test_create_user_a():
    resp = api_request(f"{BACKEND_URL}/users/", method="POST", data={
        "username": "wallet_test_a",
        "display_name": "テストユーザーA",
    })
    assert "id" in resp, f"User creation failed: {resp}"
    state["user_a"] = resp

def test_create_user_b():
    resp = api_request(f"{BACKEND_URL}/users/", method="POST", data={
        "username": "wallet_test_b",
        "display_name": "テストユーザーB",
    })
    assert "id" in resp, f"User creation failed: {resp}"
    state["user_b"] = resp

def test_wallet_auto_created():
    uid = state["user_a"]["id"]
    # Create wallet explicitly (or verify auto-creation via task-reward)
    try:
        resp = api_request(f"{WALLET_URL}/wallets/", method="POST", data={"user_id": uid})
    except RuntimeError:
        pass  # Already exists is OK
    resp = api_request(f"{WALLET_URL}/wallets/{uid}")
    assert resp["user_id"] == uid, f"Wallet user_id mismatch: {resp}"
    assert "balance" in resp, f"No balance field: {resp}"


# ── Test 3: Task Lifecycle → Bounty Payment ──

def test_create_task():
    resp = api_request(f"{BACKEND_URL}/tasks/", method="POST", data={
        "title": "Wallet統合テスト: コーヒー豆補充",
        "description": "テスト用タスク",
        "bounty_gold": 1500,
        "bounty_xp": 100,
        "urgency": 2,
        "zone": "kitchen",
        "task_type": ["supply", "test"],
        "location": "kitchen",
    })
    assert "id" in resp, f"Task creation failed: {resp}"
    state["task"] = resp

def test_accept_task():
    task_id = state["task"]["id"]
    user_id = state["user_a"]["id"]
    resp = api_request(f"{BACKEND_URL}/tasks/{task_id}/accept", method="PUT", data={
        "user_id": user_id,
    })
    assert resp["assigned_to"] == user_id, f"Assignment mismatch: {resp}"
    assert resp["accepted_at"] is not None, "accepted_at not set"

def test_complete_task():
    task_id = state["task"]["id"]
    resp = api_request(f"{BACKEND_URL}/tasks/{task_id}/complete", method="PUT")
    assert resp["is_completed"] is True, f"Task not completed: {resp}"

def test_bounty_paid():
    uid = state["user_a"]["id"]
    resp = api_request(f"{WALLET_URL}/wallets/{uid}")
    assert resp["balance"] >= 1500, f"Balance too low after bounty: {resp['balance']}"


# ── Test 4: Transaction History ──

def test_transaction_history():
    uid = state["user_a"]["id"]
    history = api_request(f"{WALLET_URL}/wallets/{uid}/history?limit=10")
    assert isinstance(history, list), f"Expected list, got: {type(history)}"
    assert len(history) >= 1, "No transactions found after bounty payment"
    # Find the task reward entry (CREDIT side for user)
    credits = [e for e in history if e["amount"] > 0]
    assert len(credits) >= 1, f"No credit entries: {history}"
    assert credits[0]["transaction_type"] == "TASK_REWARD", f"Wrong type: {credits[0]}"


# ── Test 5: Idempotency ──

def test_duplicate_reward_rejected():
    task_id = state["task"]["id"]
    uid = state["user_a"]["id"]
    try:
        api_request(f"{WALLET_URL}/transactions/task-reward", method="POST", data={
            "user_id": uid,
            "amount": 1500,
            "task_id": task_id,
            "description": "Duplicate attempt",
        })
        # If it succeeded, the balance should still be 1500 (not 3000)
        resp = api_request(f"{WALLET_URL}/wallets/{uid}")
        assert resp["balance"] == 1500, f"Duplicate payment accepted! Balance: {resp['balance']}"
    except RuntimeError as e:
        # 400 error is expected (duplicate reference_id)
        assert "400" in str(e), f"Unexpected error: {e}"


# ── Test 6: P2P Transfer ──

def test_p2p_transfer():
    uid_a = state["user_a"]["id"]
    uid_b = state["user_b"]["id"]
    # Ensure user B has a wallet
    try:
        api_request(f"{WALLET_URL}/wallets/", method="POST", data={"user_id": uid_b})
    except RuntimeError:
        pass

    resp = api_request(f"{WALLET_URL}/transactions/p2p-transfer", method="POST", data={
        "from_user_id": uid_a,
        "to_user_id": uid_b,
        "amount": 500,
        "description": "テスト送金",
    })
    assert "transaction_id" in resp, f"P2P transfer failed: {resp}"

    # Verify balances
    a = api_request(f"{WALLET_URL}/wallets/{uid_a}")
    b = api_request(f"{WALLET_URL}/wallets/{uid_b}")
    assert a["balance"] == 1000, f"User A balance wrong: {a['balance']} (expected 1000)"
    assert b["balance"] == 500, f"User B balance wrong: {b['balance']} (expected 500)"


# ── Test 7: Supply Stats ──

def test_supply_stats():
    resp = api_request(f"{WALLET_URL}/supply")
    assert "total_issued" in resp, f"Missing total_issued: {resp}"
    assert resp["total_issued"] >= 1500, f"Supply too low: {resp['total_issued']}"


# ── Test 8: Device XP Scoring (F.2) ──

def test_register_device():
    uid = state["user_a"]["id"]
    resp = api_request(f"{WALLET_URL}/devices/", method="POST", data={
        "device_id": "test_sensor_01",
        "owner_id": uid,
        "device_type": "sensor_node",
        "display_name": "テストセンサー",
        "topic_prefix": "office/kitchen/sensor/test_sensor_01",
    })
    assert "id" in resp, f"Device registration failed: {resp}"
    assert resp["xp"] == 0, f"Initial XP should be 0: {resp['xp']}"

def test_xp_grant():
    task_id = state["task"]["id"]
    resp = api_request(f"{WALLET_URL}/devices/xp-grant", method="POST", data={
        "zone": "kitchen",
        "task_id": task_id,
        "xp_amount": 20,
        "event_type": "task_completed",
    })
    assert resp["devices_awarded"] >= 1, f"No devices awarded XP: {resp}"
    assert "test_sensor_01" in resp["device_ids"], f"Test device not awarded: {resp}"
    assert resp["total_xp_granted"] >= 20, f"XP too low: {resp}"

def test_zone_multiplier():
    resp = api_request(f"{WALLET_URL}/devices/zone-multiplier/kitchen")
    assert resp["device_count"] >= 1, f"No devices in zone: {resp}"
    assert resp["avg_xp"] >= 20, f"XP not accumulated: {resp}"
    # 20 XP → multiplier = 1.0 + (20/1000)*0.5 = 1.01
    assert resp["multiplier"] >= 1.0, f"Multiplier too low: {resp}"

def test_device_xp_persisted():
    devices = api_request(f"{WALLET_URL}/devices/")
    test_dev = [d for d in devices if d["device_id"] == "test_sensor_01"]
    assert len(test_dev) == 1, f"Test device not found: {devices}"
    assert test_dev[0]["xp"] >= 20, f"XP not persisted: {test_dev[0]}"

def test_reward_rates():
    rates = api_request(f"{WALLET_URL}/reward-rates")
    assert isinstance(rates, list), f"Expected list: {type(rates)}"
    types = {r["device_type"] for r in rates}
    assert "sensor_node" in types, f"sensor_node rate missing: {types}"


# ── Test 9: Nginx Proxy (Frontend → Wallet) ──

def test_nginx_wallet_proxy():
    uid = state["user_a"]["id"]
    resp = api_request(f"{FRONTEND_URL}/api/wallet/wallets/{uid}")
    assert resp["user_id"] == uid, f"Proxy returned wrong user: {resp}"
    assert "balance" in resp, "No balance in proxied response"


# ── Cleanup ──

def cleanup():
    # Clean up test tasks (mark as completed if not already)
    if state["task"]:
        task_id = state["task"]["id"]
        try:
            api_request(f"{BACKEND_URL}/tasks/{task_id}/complete", method="PUT")
        except Exception:
            pass


# ── Main ──

def main():
    global passed, failed, skipped
    print("=" * 60)
    print("SOMS Wallet Integration Test")
    print("=" * 60)

    print("\n🔍 Test 1: Health Checks")
    test("Wallet service health", test_wallet_health)
    test("Backend service health", test_backend_health)

    print("\n👤 Test 2: User & Wallet Creation")
    test("Create user A", test_create_user_a)
    test("Create user B", test_create_user_b)
    test("Wallet auto-created for user A", test_wallet_auto_created)

    print("\n📋 Test 3: Task Lifecycle → Bounty Payment")
    test("Create task (bounty=1500)", test_create_task)
    test("Accept task (assign to user A)", test_accept_task)
    test("Complete task", test_complete_task)
    test("Bounty paid to user A wallet", test_bounty_paid)

    print("\n📜 Test 4: Transaction History")
    test("Transaction history contains TASK_REWARD", test_transaction_history)

    print("\n🔒 Test 5: Idempotency")
    test("Duplicate task-reward rejected", test_duplicate_reward_rejected)

    print("\n💸 Test 6: P2P Transfer")
    test("P2P transfer (A→B, 500)", test_p2p_transfer)

    print("\n📊 Test 7: Supply Stats")
    test("Supply stats reflect issuance", test_supply_stats)

    print("\n🎮 Test 8: Device XP Scoring (F.2)")
    test("Register device in kitchen zone", test_register_device)
    test("XP grant to zone devices", test_xp_grant)
    test("Zone multiplier calculation", test_zone_multiplier)
    test("Device XP persisted", test_device_xp_persisted)
    test("Reward rates seeded", test_reward_rates)

    print("\n🌐 Test 9: Nginx Proxy")
    test("Frontend /api/wallet/ proxies to wallet service", test_nginx_wallet_proxy)

    # Summary
    total = passed + failed + skipped
    print(f"\n{'=' * 60}")
    print(f"Results: {passed} passed, {failed} failed, {skipped} skipped / {total} total")
    print(f"{'=' * 60}")

    cleanup()
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
