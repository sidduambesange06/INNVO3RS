"""End-to-end test: 2 alerts -> all 4 drones dispatched"""
import requests
import json
import time
import sys

BASE = "http://127.0.0.1:8000"
OUT = []

def log(msg):
    try:
        print(msg)
    except UnicodeEncodeError:
        print(msg.encode('ascii', 'replace').decode())
    OUT.append(msg)

def get_drones():
    r = requests.get(f"{BASE}/drones")
    return r.json()["drones"]

def get_queue():
    r = requests.get(f"{BASE}/queue")
    return r.json()["queue"]

def get_health():
    r = requests.get(f"{BASE}/health")
    return r.json()

def fmt_drone(d):
    return f"  {d['drone_id']}: {str(d['status']):12s} bat={d['battery']:3d}% zone={str(d.get('target_zone') or '---'):8s} eta={d['eta_seconds']:6.1f}s alert={str(d.get('assigned_alert_id') or '---')}"

# Step 1: Check initial state
log("=" * 60)
log("STEP 1: Check initial state")
log("=" * 60)
h = get_health()
log(f"  Drones: {h['components']['drones']}")
drones = get_drones()
for d in drones:
    log(f"  {d['drone_id']}: {str(d['status']):12s} bat={d['battery']:3d}%")

# Step 2: Create alert in Zone-A
log("\n" + "=" * 60)
log("STEP 2: Create alert in Zone-A (crowd_anomaly, severity=0.85)")
log("=" * 60)
r = requests.post(f"{BASE}/alerts/manual", json={
    "zone_id": "Zone-A", "anomaly_type": "crowd_anomaly", "severity": 0.85
})
alert1 = r.json()
log(f"  Alert: {alert1.get('alert_id')}")
log(f"  Primary drone: {alert1.get('primary_drone')}")
log(f"  Secondary drone: {alert1.get('secondary_drone')}")
log(f"  Primary ETA: {alert1.get('primary_eta')}s")

time.sleep(2)

# Step 3: Check drone statuses
log("\n" + "=" * 60)
log("STEP 3: Drone statuses after first alert")
log("=" * 60)
drones = get_drones()
for d in drones:
    log(fmt_drone(d))

# Step 4: Create second alert in Zone-D (far away)
log("\n" + "=" * 60)
log("STEP 4: Create alert in Zone-D (weapon_detect, severity=0.95)")
log("  Waiting 31s for dedup window...")
log("=" * 60)
time.sleep(31)
r = requests.post(f"{BASE}/alerts/manual", json={
    "zone_id": "Zone-D", "anomaly_type": "weapon_detect", "severity": 0.95
})
alert2 = r.json()
log(f"  Alert: {alert2.get('alert_id')}")
log(f"  Primary drone: {alert2.get('primary_drone')}")
log(f"  Secondary drone: {alert2.get('secondary_drone')}")

time.sleep(2)

# Step 5: Check all drones
log("\n" + "=" * 60)
log("STEP 5: All drone statuses after 2 alerts")
log("=" * 60)
drones = get_drones()
active_count = 0
for d in drones:
    log(fmt_drone(d))
    if d['status'] in ('EN_ROUTE', 'REROUTING', 'HOVERING'):
        active_count += 1

log(f"\n  >> Active drones: {active_count}/4")

# Step 6: Check queue
log("\n" + "=" * 60)
log("STEP 6: Priority queue")
log("=" * 60)
queue = get_queue()
for item in queue:
    log(f"  {item['alert_id']}: sev={item['severity']:.2f} assigned={item['assigned']} dispatched={item.get('dispatched',False)} drone={str(item.get('primary_drone') or '---')}")

# Write to file
with open("scripts/test_output.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(OUT))

log("\n>> Test complete!")
