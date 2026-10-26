# QQ mobile interaction on a Linux server

Cyber Habitat and NapCat can run together in Docker Compose on one Linux host. NapCat receives private QQ messages and posts them to Cyber Habitat over Compose's private network. Cyber Habitat sends Mori's reply back through OneBot. The QQ account logged into NapCat is the bot account; `HABITAT_ONEBOT_TARGET_USER_ID` is the separate QQ account that sends messages from the phone.

The NapCat service is optional and starts only with the `qq` profile. The host publishes only Cyber Habitat on `127.0.0.1:8765` and the NapCat WebUI on `127.0.0.1:6099`. NapCat's OneBot HTTP port 5700 is not published. Access the server UI through SSH port forwarding; do not expose either web interface directly to the internet.

## Prepare server configuration

1. Copy `.env.example` to `.env` on the Linux host. Replace the three token placeholders with distinct random values. Set `HABITAT_ONEBOT_TARGET_USER_ID` to the QQ number that will message the bot from the phone. Keep `.env` private and out of Git.
2. From the project directory, start the application and NapCat with `docker compose -f compose.yaml -f compose.qq.yaml --profile qq up -d --build`.
3. Forward both local interfaces from your computer: `ssh -L 8765:127.0.0.1:8765 -L 6099:127.0.0.1:6099 <linux-user>@<server-address>`. While that SSH connection is open, visit `http://127.0.0.1:6099` and authenticate with `NAPCAT_WEBUI_TOKEN`; the Cyber Habitat page is at `http://127.0.0.1:8765`.
4. Log the dedicated bot QQ account into NapCat. The phone's QQ account must be able to send the bot a private message. If `HABITAT_ONEBOT_RESIDENT_ID` is set, it must match the resident's full current ID; leave it blank to auto-select when there is exactly one resident.

NapCat's current Linux guide documents the `mlikiowa/napcat-docker` image, WebUI port 6099, and persistent config/QQ data volumes. The optional Compose overlay follows that layout. Set `NAPCAT_IMAGE` to a specific tested tag before long-running use instead of relying on `latest`.

## Configure NapCat OneBot

In NapCat WebUI, add and enable an **HTTP Server** connection:

- Host: `0.0.0.0` (Compose's private network only; do not publish port 5700).
- Port: `5700`.
- Token: the value of `HABITAT_ONEBOT_ACCESS_TOKEN`.
- Save the connection and the full Bot configuration, then restart NapCat if requested.

Add and enable an **HTTP Client** connection for event delivery:

- URL: `http://cyber-habitat:8765/integrations/onebot/events`.
- Token: the different value of `HABITAT_ONEBOT_INBOUND_TOKEN`.
- Report private message events; keep self-message reporting disabled.
- Save the connection and full Bot configuration.

Cyber Habitat trusts only the explicit Compose service names `cyber-habitat` and `napcat` for this internal HTTP exchange. The OneBot sender must match the configured phone QQ number. Group messages and other senders are rejected. Supported messages are plain text only; media, groups, files, voice, proactive messages, and multiple users are not supported.

After both services are running, check `http://127.0.0.1:8765/integrations/onebot/status` through an SSH tunnel. It reports whether the bridge is configured without returning QQ numbers or tokens. Then send a short private message from the phone to the bot account. Mori's answer uses the configured model, and the message plus recent conversation context are sent to that model as in browser chat.

For the Docker deployment, a DeepSeek key may be entered in the browser and saved to the persistent `/app/data/.env` file, or set as `HABITAT_AI_API_KEY` in the host `.env`. Never commit the host `.env` or share tokens in chat.

The base Cyber Habitat service is deployed separately on the isolated test ECS. The optional NapCat profile is not yet running, and this document does not log into QQ automatically. Complete the protected NapCat setup and phone-message round trip before treating QQ mobile interaction as accepted.
