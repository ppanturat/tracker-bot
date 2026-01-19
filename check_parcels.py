import os
import requests
import json
from supabase import create_client

# --- CONFIGURATION ---
DISCORD_URL = os.environ.get('DISCORD_URL') 
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')
TRACK17_KEY = os.environ.get('TRACK17_KEY')

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def send_discord_message(content):
    requests.post(DISCORD_URL, json={"content": content})

def check_parcels():
    # Get active parcels (Ignore ones that are already 'Delivered')
    # We use a filter: last_status IS NOT 'Delivered'
    response = supabase.table('parcels').select("*").neq('last_status', 'Delivered').execute()
    parcels = response.data

    if not parcels:
        print("No active parcels to check.")
        return

    # Prepare Payload for 17Track
    # We create a list of numbers to check
    payload = []
    for p in parcels:
        payload.append({"number": p['tracking_number']})

    # call 17Track API
    headers = {"RF-TOKEN": TRACK17_KEY, "Content-Type": "application/json"}
    url = "https://api.17track.net/track/v2.2/gettrackinfo"

    try:
        resp = requests.post(url, json=payload, headers=headers)
        data = resp.json()
        
        if data.get("code") != 0:
            print(f"17Track API Error: {data.get('message')}")
            return
            
        track_infos = data.get("data", {}).get("accepted", [])

        # Compare and Notify
        for info in track_infos:
            number = info.get("number")
            
            # Find the matching parcel in our DB list
            # (Simple logic: find the first match)
            db_parcel = next((p for p in parcels if p['tracking_number'] == number), None)
            
            if db_parcel:
                # 17Track Status Codes: 10=InTransit, 30=Pickup, 40=Delivered, etc.
                # We prioritize the "latest_event" description for the message
                track_events = info.get("track_info", {}).get("latest_event", {})
                new_status_desc = track_events.get("context", "Unknown Status")
                
                # Check 17Track's "Package Status" category (e.g., 'Delivered')
                # If package is delivered, we want to save that specific word to stop tracking it.
                package_status_stage = info.get("track_info", {}).get("latest_status", {}).get("status")
                
                # Map stage code to text for the DB (simplified)
                stage_map = {10: "In Transit", 30: "Pick Up", 40: "Delivered", 50: "Alert"}
                current_stage_text = stage_map.get(package_status_stage, "In Transit")

                # If the description CHANGED, notify the user
                if db_parcel['last_status'] != current_stage_text:
                    
                    # Send Discord Ping
                    user_id = db_parcel['discord_user_id']
                    msg = f"📦 **Update for <@{user_id}>!**\nTracking: `{number}`\nStatus: **{current_stage_text}**\n📍 {new_status_desc}"
                    send_discord_message(msg)
                    
                    # Update Database
                    supabase.table('parcels').update({'last_status': current_stage_text}).eq('id', db_parcel['id']).execute()
                    print(f"Updated {number} to {current_stage_text}")

    except Exception as e:
        print(f"Error checking parcels: {e}")

if __name__ == "__main__":
    check_parcels()