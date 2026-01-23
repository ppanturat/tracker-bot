import os
import requests
from supabase import create_client

# --- CONFIGS ---
PARCEL_TRACK_DISCORD_URL = os.environ.get('PARCEL_TRACK_DISCORD_URL') 
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')
TRACK17_KEY = os.environ.get('TRACK17_KEY')

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def send_discord_message(content):
    if not PARCEL_TRACK_DISCORD_URL:
        print("Error: No Discord Webhook URL found.")
        return
    requests.post(PARCEL_TRACK_DISCORD_URL, json={"content": content})

def check_parcels():
    print("Checking parcels...")

    # Fetch active parcels
    response = supabase.table('parcels').select("*").neq('last_status', 'Delivered').execute()
    parcels = response.data

    if not parcels:
        return 

    # --- Data Cleanup ---
    for p in parcels:
        if p.get('tracking_number'):
            p['tracking_number'] = p['tracking_number'].strip().upper()

    # Prepare Payload
    payload = [{"number": p['tracking_number']} for p in parcels]

    # Call 17Track API
    headers = {"17token": TRACK17_KEY, "Content-Type": "application/json"}
    url = "https://api.17track.net/track/v2.2/gettrackinfo"

    try:
        resp = requests.post(url, json=payload, headers=headers)
        data = resp.json()
        
        if data.get("code") != 0:
            print(f"17Track API Error: {data.get('message')}")
            return
            
        raw_data = data.get("data", [])
        if isinstance(raw_data, dict):
            track_infos = raw_data.get("accepted", [])
        else:
            track_infos = raw_data

        # Compare and Notify
        for info in track_infos:
            if not isinstance(info, dict):
                continue

            number = info.get("number")
            
            # Find matching parcel in DB
            db_parcel = next((p for p in parcels if p['tracking_number'] == number), None)
            
            if db_parcel:
                track_info = info.get("track_info", {})
                latest_event = track_info.get("latest_event", {})
                latest_status = track_info.get("latest_status", {})
                
                # 1. Get Description (e.g. "Arrived at Sorting Center")
                description = latest_event.get("context")
                if not description:
                    description = latest_event.get("status_description")

                # 2. Get Stage Code
                stage_code = latest_status.get("status")

                # 3. Fallback if description is empty
                if not description:
                    status_map = {
                        0: "Registered",
                        10: "In Transit",
                        30: "Ready for Pickup",
                        40: "Delivered",
                        50: "Alert"
                    }
                    description = status_map.get(stage_code, "Tracking...")

                # 4. Get Location (The missing piece!)
                location = latest_event.get("location")

                # 5. Combine: "Description, Location"
                if location:
                    # Cleans up cases where location might be redundant or empty
                    current_status = f"{description}, {location}"
                else:
                    current_status = description

                # Clean up length
                current_status = current_status[:200]

                # Special Case: Delivered
                if stage_code == 40:
                    current_status = "Delivered"

                # Check for CHANGE
                if db_parcel['last_status'] != current_status:
                    user_id = db_parcel['discord_user_id']
                    
                    emoji = "🚚"
                    if stage_code == 0: emoji = "📮"
                    if stage_code == 30: emoji = "📦"
                    if stage_code == 40: emoji = "✅"
                    if stage_code == 50: emoji = "⚠️"
                    
                    msg = f"{emoji} **Update for <@{user_id}>!**\nTracking: `{number}`\nStatus: **{current_status}**"
                    send_discord_message(msg)
                    
                    supabase.table('parcels').update({'last_status': current_status}).eq('id', db_parcel['id']).execute()
                    print(f"Updated {number} to: {current_status}")
                
    except Exception as e:
        print(f"Error checking parcels: {e}")

if __name__ == "__main__":
    check_parcels()
