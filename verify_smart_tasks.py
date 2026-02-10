
import requests
import time
import sys
from datetime import datetime, timedelta, timezone

def check():
    # 1. Create Task A
    print("Creating Task A...")
    try:
        r = requests.post("http://localhost:8000/tasks/", json={
            "title": "Task A",
            "description": "Desc A",
            "bounty_gold": 100,
            "bounty_xp": 0,
            "task_type": "general",
            "expires_at": None,
            "location": "Office"
        })
        if r.status_code != 200:
            print(f"Failed to create Task A: {r.status_code} {r.text}")
            return False
        t1 = r.json()
        print(f"Task A created: ID={t1['id']}")
    except Exception as e:
        print(f"Connection failed: {e}")
        return False

    # 2. Duplicate Check
    print("Creating Task A again (Duplicate)...")
    r = requests.post("http://localhost:8000/tasks/", json={
        "title": "Task A",
        "description": "Desc A Duplicate",
        "bounty_gold": 200,
        "bounty_xp": 0,
        "task_type": "general",
        "expires_at": None,
        "location": "Office"
    })
    if r.status_code != 200:
        print(f"Failed to create Duplicate Task A: {r.status_code} {r.text}")
        return False
    t2 = r.json()
    print(f"Task A Duplicate created: ID={t2['id']}")

    # Check count
    r = requests.get("http://localhost:8000/tasks/")
    tasks = r.json()
    print(f"Total tasks: {len(tasks)}")
    
    # We expect 1 task (Task A Duplicate)
    # Note: If there were other tasks from before, this might fail, but we're assuming clean DB.
    # Actually, verify that t1['id'] is NOT in the list (deleted) and t2['id'] IS.
    
    current_ids = [t['id'] for t in tasks]
    if t1['id'] in current_ids and t1['id'] != t2['id']:
        print("ERROR: Old task was NOT deleted!")
        return False
    
    target_task = next((t for t in tasks if t['id'] == t2['id']), None)
    if not target_task:
        print("ERROR: New task not found?")
        return False
        
    if target_task['description'] != "Desc A Duplicate":
        print(f"ERROR: Description not updated? Got: {target_task['description']}")
        return False

    # 3. Expiration Check
    print("Creating Expiring Task B...")
    expires_at = (datetime.now(timezone.utc) + timedelta(seconds=2)).isoformat()
    
    r = requests.post("http://localhost:8000/tasks/", json={
        "title": "Task B",
        "description": "Expiring",
        "bounty_gold": 50,
        "bounty_xp": 0,
        "task_type": "short",
        "expires_at": expires_at,
        "location": "Office"
    })
    if r.status_code != 200:
        print(f"Failed to create Task B: {r.status_code} {r.text}")
        return False
    t3 = r.json()
    print(f"Task B created: ID={t3['id']}")

    print("Waiting 4 seconds for expiration...")
    time.sleep(4)

    r = requests.get("http://localhost:8000/tasks/")
    tasks = r.json()
    print(f"Total tasks after wait: {len(tasks)}")
    
    ids = [t['id'] for t in tasks]
    if t3['id'] in ids:
        print("ERROR: Task B should be expired and hidden!")
        return False
    
    print("SUCCESS: Smart Task Management Verified.")
    return True

if __name__ == "__main__":
    if not check():
        sys.exit(1)
