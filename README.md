# getTeamsRecordings
Python script leveraging Graph API to search all chats and channels within a given time span to report recording data, including the recording location and the initiator of the recording. 

# Permissions required
This application uses the following Application-based permissions:

| Permission Name |	Description |
| --------------- | ----------- |
| Chat.Read.All |	Read all 1:1 and group chat messages in the organization |
| ChatMessage.Read.All	| Read all chat messages (required for message content access) |
| OnlineMeetingArtifact.Read.All	| Read meeting artifacts like recordings and transcripts (optional but recommended) |
| User.Read.All	| Read all users' full profiles |
| Team.ReadBasic.All	| Read names and IDs of all teams |
| ChannelMessage.Read.All	| Read all channel messages in all teams |
