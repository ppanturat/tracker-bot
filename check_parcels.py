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
    headers = {"17token": TRACK17_KEY, "Content-Type": "application/json"}
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
                track_info = info.get("track_info", {})
                latest_event = track_info.get("latest_event", {})
                latest_status = track_info.get("latest_status", {})
                current_status = latest_event.get("context")
                
                if not current_status:
                    current_status = latest_event.get("status_description")
                
                if not current_status:
                    stage = latest_status.get("status") # This is "InTransit"
                    
                    # Map both Strings (New API) and Integers (Old API)
                    status_map = {
                        # String Values
                        "NotFound": "Registered (Waiting for Scan)",
                        "InfoReceived": "Registered (Info Received)",
                        "InTransit": "In Transit (Moving)",
                        "Expired": "Expired",
                        "AvailableForPickup": "Ready for Pickup",
                        "OutForDelivery": "Out for Delivery",
                        "DeliveryFailure": "Delivery Failed",
                        "Delivered": "Delivered Successfully",
                        "Exception": "Alert / Exception",
                        
                        # Integer Fallbacks (Just in case)
                        0: "Registered",
                        10: "In Transit",
                        30: "Ready for Pickup",
                        40: "Delivered"
                    }
                    
                    # Get the clean text, or default to "Tracking (InTransit)" if unknown
                    current_status = status_map.get(stage, f"Tracking ({stage})")

                # Check for change
                if db_parcel['last_status'] != current_status:
                    
                    user_id = db_parcel['discord_user_id']
                    
                    # Pick Emoji
                    stage = latest_status.get("status")
                    emoji = "🚚"
                    if stage == 0: emoji = "📮"
                    if stage == 30: emoji = "📦"
                    if stage == 40: emoji = "✅"
                    if stage == 50: emoji = "⚠️"
                    
                    msg = f"{emoji} **Update for <@{user_id}>!**\nTracking: `{number}`\nStatus: **{current_status}**"
                    send_discord_message(msg)
                    
                    # Update DB
                    supabase.table('parcels').update({'last_status': current_status}).eq('id', db_parcel['id']).execute()
                    print(f"Updated {number} to: {current_status}")

    except Exception as e:
        print(f"Error checking parcels: {e}")

if __name__ == "__main__":
    check_parcels()
