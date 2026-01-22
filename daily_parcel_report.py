import os
import requests
from supabase import create_client

# --- CONFIGS ---
PARCEL_DISCORD_URL = os.environ.get('PARCEL_TRACK_DISCORD_URL') 
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')
TRACK17_KEY = os.environ.get('TRACK17_KEY')

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def send_discord_message(content):
    if not PARCEL_DISCORD_URL:
        print("Error: No Discord Webhook URL found.")
        return
    requests.post(PARCEL_DISCORD_URL, json={"content": content})

def run_daily_report():
    print("Running Daily Report...")

    # Fetch all parcels
    response = supabase.table('parcels').select("*").execute()
    parcels = response.data

    if not parcels:
        print("No parcels to report. Exiting.")
        return 

    # Ask 17Track for latest info
    payload = [{"number": p['tracking_number']} for p in parcels]
    headers = {"17token": TRACK17_KEY, "Content-Type": "application/json"}
    
    try:
        # Note: 'gettrackinfo' returns the list directly in 'data', not 'accepted'
        resp = requests.post("https://api.17track.net/track/v2.2/gettrackinfo", json=payload, headers=headers)
        api_data = resp.json()
        
        if api_data.get("code") != 0:
            print(f"API Error: {api_data.get('message')}")
            return
            
        track_infos = api_data.get("data", [])
        
    except Exception as e:
        print(f"Connection Error: {e}")
        return

    message_lines = []
    ids_to_delete = []

    for info in track_infos:
        number = info.get("number")
        track_info = info.get("track_info", {})
        latest_event = track_info.get("latest_event", {})
        latest_status = track_info.get("latest_status", {})
        
        description = latest_event.get("context")
        
        # If empty, try the standard description (e.g. "In Transit")
        if not description:
            description = latest_event.get("status_description")
            
        # If STILL empty, map the code manually
        if not description:
            stage = latest_status.get("status")
            status_map = {
                0: "Registered (Waiting for Scan)",
                10: "In Transit",
                30: "Ready for Pickup",
                40: "Delivered",
                50: "Exception / Alert"
            }
            description = status_map.get(stage, "Tracking...")

        # Get Location (if available)
        location = latest_event.get("location")
        loc_str = f" *({location})*" if location else ""

        # Map Emoji based on Stage
        stage = latest_status.get("status")
        emoji = "🚚"
        if stage == 0: emoji = "📮"   # Registered
        if stage == 30: emoji = "📦"  # Pickup
        if stage == 40: emoji = "✅"  # Delivered
        if stage == 50: emoji = "⚠️"  # Alert

        # Format: 🚚 `ED123...` : Arrived at Sorting Center (Bangkok)
        line = f"{emoji} `{number}` : {description}{loc_str}"
        message_lines.append(line)

        # Mark for deletion if Delivered
        if stage == 40 or "Delivered" in str(stage):
            ids_to_delete.append(number)

    if message_lines:
        final_msg = "**🌅 Daily Parcel Summary**\n" + "\n".join(message_lines)
        
        if ids_to_delete:
            final_msg += "\n\n🧹 **Auto-Cleaning:** Delivered parcels have been removed."

        send_discord_message(final_msg)
        print("Report sent to Discord.")

    if ids_to_delete:
        for num in ids_to_delete:
            supabase.table('parcels').delete().eq('tracking_number', num).execute()
            print(f"Removed {num} from database.")

if __name__ == "__main__":
    run_daily_report()