# 两人小屋

这是独立的双人文字房间。两台设备连同一台宿主机，消息存到房主电脑的 `data/duo.sqlite3`。它不会把房间消息发给 AI，也不访问 Mori 的私聊、备忘、世界记录和模型密钥。

## 同一台电脑

在项目目录双击 `Start-Duo.cmd`。窗口会显示 `Seat 1, local` 和 `Seat 2, local` 两条邀请链接。分别在两个浏览器（或普通窗口和隐私窗口）打开。开始使用后保留黑窗口。数据库保存在项目目录，重新启动后邀请和消息历史都保留。

## 异地使用

1. 在房主电脑和对方设备上安装 Tailscale，登录后由房主邀请对方的账号加入私人网络，并确认只有你们能访问该电脑。
2. 房主电脑执行 `tailscale serve --bg --https=8443 http://127.0.0.1:8766`，记下输出的私网 HTTPS 地址。参考 [Tailscale Serve](https://tailscale.com/docs/reference/tailscale-cli/serve)。不要使用 Funnel，也不用在路由器上转发端口。
3. 关闭原来的房间窗口，在 CMD 从项目目录运行 `Start-Duo.cmd --origin https://你的私网地址:8443`，用实际地址替换示例。窗口会为两个座位各打印一个 `private link`；自己留一个，另一个私下发给对方。房主电脑和房间程序都要保持运行。
4. 暂停时关闭房间窗口。要移除刚才的 Serve 转发规则，执行 `tailscale serve --bg --https=8443 off`（如果已有其他 Serve 服务，先用 `tailscale serve status` 确认规则）。

邀请链接等同于房间密码。同一条链接可以从多台设备打开，因此不要把链接发到群里。链接的密钥部分位于 `#` 后，页面用它设置请求的 Authorization 头。TLS 由私网入口处理；房主电脑可读取本地 SQLite 聊天记录。

## 协议

- `GET /` 提供页面，页面不含房间数据。
- `GET /api/messages?after=序号`：携带 `Authorization: Bearer <邀请密钥>`；首次返回最近 100 条，后续按序号增量拉取，每批最多 100 条。
- `POST /api/messages`：使用同样的授权头和 JSON `{"text":"内容"}`；座位由服务端根据密钥决定。成功返回 201 和消息序号。
- 前台每 1.5 秒拉一次，回到页面时立即同步。无 WebSocket、聊天室账号系统或消息推送。当前只有两个座位和一个房间；没有群聊或角色群聊。Mori 主页的本机入口不会开放原有服务。
