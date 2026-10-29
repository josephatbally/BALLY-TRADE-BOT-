# BALLY FLOW — Cloudflare remote phone access

This guide connects the React Native Android app to the FastAPI backend on the Windows PC when the phone is using mobile data or another Wi-Fi network. Cloudflare Tunnel creates an outbound connection, so router port forwarding is not required.

## What the repository currently uses

- The mobile API base URL is hard-coded in `mobile/src/api/config.ts` as `http://192.168.1.136:8000`.
- The mobile client adds its stored JWT as an `Authorization: Bearer` header.
- The backend health endpoint is `/health`; the expected local API origin is port `8000`.

A tunnel by itself does **not** update the installed app's URL. After obtaining a tunnel hostname, set `API_BASE_URL` to that HTTPS hostname and rebuild/reinstall the Android app.

## Option A — quick test (temporary URL)

1. On the Windows PC, start the existing BALLY FLOW backend from the project root using the launch command you already use. Do not start a second Uvicorn process if one is already serving port 8000.
2. Confirm `http://127.0.0.1:8000/health` responds on the PC.
3. Install `cloudflared` for Windows from the [official download instructions](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/).
4. From the repository root, run:

   ```powershell
   .\scripts\start-cloudflare-tunnel.ps1
   ```

   Or run the equivalent command directly:

   ```powershell
   cloudflared tunnel --url http://127.0.0.1:8000
   ```

5. Copy the generated `https://....trycloudflare.com` URL from the terminal. Keep the tunnel process running.
6. In `mobile/src/api/config.ts`, change the base URL to the exact generated HTTPS URL, for example:

   ```ts
   export const API_BASE_URL = 'https://your-generated-host.trycloudflare.com';
   ```

   Replace the example with your actual URL. Do not append `/health`; API functions already append their paths.
7. From `mobile/`, run the project's normal Android release build, then install the newly built APK on the physical phone. Test the app using mobile data or a different Wi-Fi network.
8. Stop the tunnel with Ctrl+C when finished. The URL is temporary and may change on the next run.

## Option B — stable hostname (recommended for ongoing use)

1. Use a domain managed by Cloudflare (or move the domain's DNS to Cloudflare).
2. In Cloudflare Dashboard, open **Networking → Tunnels**, create a named tunnel, and install/run its Windows connector using the command Cloudflare provides.
3. Add a **Published application** route such as `api.your-domain.example` pointing to `http://localhost:8000`. Cloudflare should create the DNS route for the tunnel.
4. Set `API_BASE_URL` in `mobile/src/api/config.ts` to `https://api.your-domain.example`, rebuild, and reinstall the app.
5. Run the named tunnel as a Windows service or other supervised process so it reconnects after restarts.

Official instructions: [Set up Cloudflare Tunnel](https://developers.cloudflare.com/tunnel/get-started/).

## Security requirements before exposing trading endpoints

- Keep the MT5 execution controls and backend authorization enabled. A tunnel is transport, not authentication.
- Confirm protected endpoints reject requests without a valid JWT and that role/permission checks are enforced server-side. Never rely on the mobile app alone to protect trading actions.
- Keep live trading disabled while validating remote connectivity; do not change execution flags as part of tunnel setup.
- Do not put Cloudflare tunnel tokens, API tokens, JWT secrets, passwords, or account credentials in source control or the mobile app.
- A public Quick Tunnel URL can be used by anyone who discovers it. Cloudflare Access email OTP is useful for browser-only testing, but interactive Access login is not a drop-in solution for this app's native API client. For ongoing production access, design and test an app-compatible access policy and rate limiting.
- Verify that `/health` is safe to expose and that error responses do not disclose secrets.

## Validation checklist

- [ ] Backend `/health` returns a successful response locally.
- [ ] Cloudflare Tunnel shows as connected / the Quick Tunnel URL responds.
- [ ] On the phone's external network, `https://YOUR-HOST/health` responds.
- [ ] The app has been rebuilt with the HTTPS base URL.
- [ ] Login succeeds and protected endpoints return expected authenticated responses.
- [ ] Requests without a valid JWT are rejected by protected routes.
- [ ] Trading remains disabled during connectivity testing.

## Troubleshooting

- **502 / connection refused:** ensure the API is listening on port 8000 and the tunnel points to `http://127.0.0.1:8000`.
- **Phone still uses LAN IP:** rebuild and reinstall after changing `mobile/src/api/config.ts`; changing the source alone does not update an installed APK.
- **Tunnel URL stops working:** Quick Tunnels only exist while the `cloudflared` process is running.
- **Authentication fails remotely:** inspect the backend logs and verify the JWT header is sent; do not disable backend authentication to make the tunnel work.
