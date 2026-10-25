# QQ mobile interaction through OneBot

Cyber Habitat can optionally communicate with one QQ account through a **local OneBot v11-compatible bridge**. The QQ client remains on the phone; the bridge runs on this computer and forwards only private messages from the configured QQ number to one resident. This repository does not install a QQ bridge, log into QQ, or send any QQ message until the local bridge is configured.

## Local configuration

Add the following ignored entries to `.env` next to the project. Do not commit this file.

```dotenv
HABITAT_ONEBOT_URL=http://127.0.0.1:5700
HABITAT_ONEBOT_ACCESS_TOKEN=onebot-outbound-token
HABITAT_ONEBOT_INBOUND_TOKEN=long-random-token-for-callbacks
HABITAT_ONEBOT_TARGET_USER_ID=your-qq-number
# Optional with one resident; required if the world has several residents.
HABITAT_ONEBOT_RESIDENT_ID=mori
```

`HABITAT_ONEBOT_URL` must be loopback HTTP. The service rejects remote OneBot URLs. Use distinct inbound and outbound tokens.

## OneBot side

Configure the bridge to:

1. expose its OneBot HTTP API only at the loopback URL above;
2. call `POST http://127.0.0.1:8765/integrations/onebot/events` for incoming events;
3. include `Authorization: Bearer <HABITAT_ONEBOT_INBOUND_TOKEN>` on that callback;
4. forward private-message events.

Only the configured QQ number is accepted. Group messages, other senders, invalid event shapes, and callbacks without the inbound token are rejected. A valid QQ message goes to the selected resident's normal conversation path; Mori's reply is sent back through OneBot's `send_private_msg` API. The incoming text, selected recent resident context, and reply use the configured DeepSeek model in the same way as the browser chat.

Check `GET /integrations/onebot/status` after restart. It returns only whether the bridge is configured and the selected resident id, never QQ numbers or tokens.

## Limits

This is a local bridge contract, not a bundled QQ bot. Run a compatible bridge only with an account and deployment arrangement you are authorized to use. Cyber Habitat does not currently support groups, images, files, voice, unsolicited QQ notifications, or multiple QQ users.
