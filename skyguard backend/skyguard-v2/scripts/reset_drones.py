"""Reset all drones to IDLE with 100% battery at home base."""
import asyncio
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

async def main():
    from app.db.database import init_db, close_db
    from app.db.crud import execute
    await init_db("data/skyguard_v2.db")
    await execute("UPDATE drones SET battery=100, status='IDLE', current_lat=home_lat, current_lon=home_lon")
    print("✅ All drones reset to IDLE with 100% battery")
    await close_db()

asyncio.run(main())
