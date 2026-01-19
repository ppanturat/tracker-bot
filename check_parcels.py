import os
import requests
from supabase import create_client

# --- CONFIGURATION ---
# Using the variable names from your snippet
PARCEL_TRACK_DISCORD_URL = os.environ.get('PARCEL_TRACK_DISCORD_URL') 
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')
TRACK17_KEY = os.environ.get('TRACK17_KEY')

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def send_discord_message(content):
    requests.post(PARCEL_TRACK_DISCORD_URL, json={"content": content})

def check_parcels():
    # 1. Fetch active parcels
    # logic: Get everything that is NOT strictly 'Delivered'
    response = supabase.table('parcels').select("*").neq('last_status', 'Delivered').execute()
    parcels = response.data

    if not parcels:
        # Silent exit (Internal check only)
        return

    # 2. Prepare Payload for 17Track
    payload = [{"number": p['tracking_number']} for p in parcels]

    # 3. Call 17Track API
    headers = {"RF-TOKEN": TRACK17_KEY, "Content-Type": "application/json"}
    url = "https://api.17track.net/track/v2.2/gettrackinfo"

    try:
        resp = requests.post(url, json=payload, headers=headers)
        data = resp.json()
        
        if data.get("code") != 0:
            print(f"17Track API Error: {data.get('message')}")
            return
            
        track_infos = data.get("data", {}).get("accepted", [])

        # 4. Compare and Notify
        for info in track_infos:
            number = info.get("number")
            
            # Find matching parcel in DB
            db_parcel = next((p for p in parcels if p['tracking_number'] == number), None)
            
            if db_parcel:
                # Get the detailed context (e.g. "Arrived at Sorting Center")
                track_events = info.get("track_info", {}).get("latest_event", {})
                latest_detail = track_events.get("context", "Unknown Status")
                
                # Get the generic stage (10=InTransit, 40=Delivered)
                stage = info.get("track_info", {}).get("latest_status", {}).get("status")

                # --- NEW LOGIC ---
                # Determine what status string we want to save/compare
                if stage == 40:
                    # If Delivered, force status to "Delivered" so the DB filter stops checking it next time
                    current_status = "Delivered"
                else:
                    # Otherwise, use the DETAILED description so we get updates on every move
                    current_status = latest_detail

                # Clean up: 17Track sometimes sends long details, truncate if needed
                current_status = current_status[:200] if current_status else "In Transit"

                # Check if it CHANGED since the last time we checked
                if db_parcel['last_status'] != current_status:
                    
                    # 🔔 IT CHANGED! Send Message for THIS parcel only.
                    user_id = db_parcel['discord_user_id']
                    
                    # Pick an emoji based on stage
                    emoji = "🚚"
                    if stage == 10: emoji = "🚛" # Moving
                    if stage == 30: emoji = "📦" # Pickup
                    if stage == 40: emoji = "✅" # Delivered
                    
                    msg = f"{emoji} **Update for <@{user_id}>!**\nTracking: `{number}`\nStatus: **{current_status}**"
                    send_discord_message(msg)
                    
                    # Update Database so we don't notify again for this specific step
                    supabase.table('parcels').update({'last_status': current_status}).eq('id', db_parcel['id']).execute()
                    print(f"Updated {number} to: {current_status}")
                
                # If statuses match (db_parcel['last_status'] == current_status):
                # We do NOTHING. The bot stays silent.

    except Exception as e:
        print(f"Error checking parcels: {e}")

if __name__ == "__main__":
    check_parcels()