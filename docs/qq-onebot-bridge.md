# QQ mobile interaction on a Linux server

Cyber Habitat and NapCat can run together in Docker Compose on one Linux host. NapCat receives private QQ messages and posts them to Cyber Habitat over Compose's private network. Cyber Habitat sends Mori's reply back through OneBot. The QQ account logged into NapCat is the bot account; `HABITAT_ONEBOT_TARGET_USER_ID` is the separate QQ account that sends messages from the phone.

The NapCat service is optional and starts only with the `qq` profile. The host publishes only Cyber Habitat on `127.0.0.1:8765` and the NapCat WebUI on `127.0.0.1:6099`. NapCat's OneBot HTTP port 5700 is not published. Access the server UI through SSH or Alibaba Cloud Session Manager port forwarding; do not expose either web interface directly to the internet.

## Secure access to the UI

Use SSH port forwarding when a working SSH key is available. For an ECS instance with Alibaba Cloud Session Manager enabled, the official `ali-instance-cli` can forward the loopback-only UI to this computer. For example, use two terminals to forward server ports `8765` and `6099` to local ports `18765` and `16099`, then visit `http://127.0.0.1:16099` and `http://127.0.0.1:18765`. Keep the tunnel processes open. Do not expose either UI or OneBot port 5700 publicly.

The test ECS currently reports Session Manager disabled; its account holder must enable Session Manager in the ECS console before that tunnel can start. This requirement is specific to that ECS account and is not an application configuration value.

## Prepare server configuration

1. Copy `.env.example` to `.env` on the Linux host. Replace the three token placeholders with distinct random values. Set `HABITAT_ONEBOT_TARGET_USER_ID` to the QQ number that will message the bot from the phone. Keep `.env` private and out of Git.
2. From the project directory, start the application and NapCat with `docker compose -f compose.yaml -f compose.qq.yaml --profile qq up -d --build`.
3. Forward both local interfaces using a secure tunnel. With SSH, map server ports 8765 and 6099 to local ports 18765 and 16099. With Session Manager enabled, use `ali-instance-cli portforward -i <instance-id> -r 8765 -l 18765` and `ali-instance-cli portforward -i <instance-id> -r 6099 -l 16099` in separate terminals. Keep both tunnel processes open. Visit `http://127.0.0.1:16099` for NapCat and `http://127.0.0.1:18765` for the app; authenticate the NapCat WebUI with `NAPCAT_WEBUI_TOKEN`.
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

The base service and NapCat profile are running on the isolated test ECS. NapCat's WebUI responds on server loopback, and the Cyber Habitat OneBot status is configured with Mori's full resident ID. NapCat's OneBot HTTP Server/Client connections have not been configured; no bot account has been QR-logged in, and no phone-message round trip has passed. Session Manager is disabled for this ECS, so the account holder must enable it in the ECS console before using that tunnel. Keep the WebUI and OneBot private until then.
