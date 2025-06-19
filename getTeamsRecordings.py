import requests
import msal
import time
from datetime import datetime, timedelta, timezone

# === CONFIGURATION ===
TENANT_ID = '{Your-Tenant-ID}'
CLIENT_ID = '{Your-Client-ID}'
CLIENT_SECRET = '{Your-Client-Secret}'
AUTHORITY = f'https://login.microsoftonline.com/{TENANT_ID}'
SCOPE = ['https://graph.microsoft.com/.default']
GRAPH_API_ENDPOINT = 'https://graph.microsoft.com/v1.0'

# === AUTHENTICATION ===
def get_access_token():
    app = msal.ConfidentialClientApplication(
        CLIENT_ID,
        authority=AUTHORITY,
        client_credential=CLIENT_SECRET
    )
    result = app.acquire_token_for_client(scopes=SCOPE)
    if "access_token" in result:
        return result['access_token']
    else:
        raise Exception(f"Auth failed: {result.get('error_description')}")

# === HANDLE API REQUESTS WITH RETRY ===
def make_api_call(url, headers):
    while True:
        response = requests.get(url, headers=headers)
        if response.status_code == 429:
            retry_after = int(response.headers.get('Retry-After', 1))
            print(f"Throttled. Retrying after {retry_after} seconds.")
            time.sleep(retry_after)
        else:
            response.raise_for_status()
            return response.json()

# === GET ALL USERS ===
def get_all_users(access_token):
    url = f"{GRAPH_API_ENDPOINT}/users"
    headers = {"Authorization": f"Bearer {access_token}"}
    users = []
    while url:
        data = make_api_call(url, headers)
        users.extend(data.get('value', []))
        url = data.get('@odata.nextLink')
    return users

# === GET CHATS FOR USER ===
def get_user_chats(access_token, user_id):
    url = f"{GRAPH_API_ENDPOINT}/users/{user_id}/chats"
    headers = {"Authorization": f"Bearer {access_token}"}
    chats = []
    while url:
        data = make_api_call(url, headers)
        chats.extend(data.get('value', []))
        url = data.get('@odata.nextLink')
    return chats

# === GET MESSAGES FROM CHAT ===
def get_recent_messages(access_token, user_id, chat_id, since_datetime):
    url = f"{GRAPH_API_ENDPOINT}/users/{user_id}/chats/{chat_id}/messages"
    headers = {"Authorization": f"Bearer {access_token}"}
    messages = []
    while url:
        data = make_api_call(url, headers)
        for msg in data.get('value', []):
            if 'eventDetail' in msg and msg['lastModifiedDateTime'] >= since_datetime:
                messages.append(msg)
        url = data.get('@odata.nextLink')
    return messages

# === GET ALL TEAMS ===
def get_all_teams(access_token):
    url = f"{GRAPH_API_ENDPOINT}/teams"
    headers = {"Authorization": f"Bearer {access_token}"}
    teams = []
    while url:
        data = make_api_call(url, headers)
        teams.extend(data.get('value', []))
        url = data.get('@odata.nextLink')
    return teams

# === GET CHANNELS FOR TEAM ===
def get_team_channels(access_token, team_id):
    url = f"{GRAPH_API_ENDPOINT}/teams/{team_id}/channels"
    headers = {"Authorization": f"Bearer {access_token}"}
    channels = []
    while url:
        data = make_api_call(url, headers)
        channels.extend(data.get('value', []))
        url = data.get('@odata.nextLink')
    return channels

# === GET MESSAGES FROM CHANNEL ===
def get_channel_messages(access_token, team_id, channel_id, since_datetime):
    url = f"{GRAPH_API_ENDPOINT}/teams/{team_id}/channels/{channel_id}/messages"
    headers = {"Authorization": f"Bearer {access_token}"}
    messages = []
    while url:
        data = make_api_call(url, headers)
        for msg in data.get('value', []):
            if 'eventDetail' in msg and msg['lastModifiedDateTime'] >= since_datetime:
                messages.append(msg)
        url = data.get('@odata.nextLink')
    return messages

# === FIND RECORDING EVENTS ===
def extract_recording_events(messages):
    recordings = []
    for msg in messages:
        event_detail = msg.get('eventDetail')
        if event_detail and event_detail.get('@odata.type') == '#microsoft.graph.callRecordingEventMessageDetail':
            recordings.append(event_detail)
    return recordings

# === GET USER DETAILS ===
def get_user_details(access_token, user_id):
    url = f"{GRAPH_API_ENDPOINT}/users/{user_id}"
    headers = {"Authorization": f"Bearer {access_token}"}
    return make_api_call(url, headers)

# === MAIN WORKFLOW ===
def main():
    days_to_search = int(input("Enter the number of days to search for recordings: "))
    since_datetime = (datetime.now(timezone.utc) - timedelta(days=days_to_search)).isoformat()
    reported_recordings = set()

    access_token = get_access_token()
    users = get_all_users(access_token)

    # Search user chats
    for user in users:
        user_id = user.get('id')
        chats = get_user_chats(access_token, user_id)
        for chat in chats:
            chat_id = chat.get('id')
            messages = get_recent_messages(access_token, user_id, chat_id, since_datetime)
            recordings = extract_recording_events(messages)
            for recording in recordings:
                recording_url = recording.get('callRecordingUrl')
                if recording_url in reported_recordings:
                    continue
                reported_recordings.add(recording_url)
                initiator = recording.get('initiator', {}).get('user', {})
                initiator_id = initiator.get('id')
                if initiator_id:
                    user_details = get_user_details(access_token, initiator_id)
                    print("Recording found:")
                    print(f"  Chat ID: {chat_id}")
                    print(f"  Initiated by: {user_details.get('displayName')} ({user_details.get('mail')})")
                    print(f"  Job Title: {user_details.get('jobTitle')}")
                    print(f"  Department: {user_details.get('department')}")
                    print(f"  Recording URL: {recording_url}")
                    print("-" * 50)

    # Search team channels
    teams = get_all_teams(access_token)
    for team in teams:
        team_id = team.get('id')
        channels = get_team_channels(access_token, team_id)
        for channel in channels:
            channel_id = channel.get('id')
            messages = get_channel_messages(access_token, team_id, channel_id, since_datetime)
            recordings = extract_recording_events(messages)
            for recording in recordings:
                recording_url = recording.get('callRecordingUrl')
                if recording_url in reported_recordings:
                    continue
                reported_recordings.add(recording_url)
                initiator = recording.get('initiator', {}).get('user', {})
                initiator_id = initiator.get('id')
                if initiator_id:
                    user_details = get_user_details(access_token, initiator_id)
                    print("Recording found:")
                    print(f"  Team ID: {team_id}")
                    print(f"  Channel ID: {channel_id}")
                    print(f"  Initiated by: {user_details.get('displayName')} ({user_details.get('mail')})")
                    print(f"  Job Title: {user_details.get('jobTitle')}")
                    print(f"  Department: {user_details.get('department')}")
                    print(f"  Recording URL: {recording_url}")
                    print("-" * 50)

if __name__ == "__main__":
    main()
