import requests, json

# Check drone statuses
r = requests.get('http://127.0.0.1:8000/drones')
d = r.json()

with open('scripts/status_output.txt', 'w') as f:
    f.write("=== DRONE STATUSES ===\n")
    for x in d['drones']:
        line = f"  {x['drone_id']}: {x['status']:12s}  bat={x['battery']:3d}%  zone={x.get('target_zone', '-')}  eta={x['eta_seconds']}s  alert={x.get('assigned_alert_id', '-')}\n"
        f.write(line)

    f.write("\n")

    # Check queue
    r2 = requests.get('http://127.0.0.1:8000/queue')
    q = r2.json()
    f.write("=== PRIORITY QUEUE ===\n")
    for item in q['queue']:
        f.write(f"  {item['alert_id']}: sev={item['severity']:.2f}  assigned={item['assigned']}  dispatched={item.get('dispatched',False)}  drone={item.get('primary_drone','-')}\n")

    f.write("\n")

    # Check health
    r3 = requests.get('http://127.0.0.1:8000/health')
    h = r3.json()
    f.write("=== HEALTH ===\n")
    f.write(json.dumps(h, indent=2))

print("Output written to scripts/status_output.txt")
