# Brevo transactional email setup

RivalXI sends OTP and selected notification emails through Brevo's transactional email REST API. No Brevo SDK or SMTP credential is required.

## 1. Brevo account setup

1. In Brevo, open **Settings → Senders, Domains & Dedicated IPs**.
2. Authenticate the domain you intend to send from. Brevo will provide DNS records to add at your DNS host.
3. Create a sender such as `RivalXI <no-reply@yourdomain.com>` and complete verification if Brevo requests it.
4. Open **Settings → SMTP & API → API Keys** and create or copy a v3 API key.
5. Make sure transactional email is activated for the Brevo account.

The sender in the application configuration must exactly match a sender that Brevo permits. Domain authentication is strongly recommended for delivery and is required by major mailbox providers in many sending scenarios.

## 2. Application configuration

Add these values to `backend/.env` for development and to the selected production environment file for deployment:

```dotenv
BREVO_API_KEY=xkeysib-your-real-key
BREVO_SENDER_EMAIL=no-reply@yourdomain.com
BREVO_SENDER_NAME=RivalXI
```

Keep the API base URL and timeout defaults unless there is a specific reason to override them:

```dotenv
# BREVO_API_BASE_URL=https://api.brevo.com
# BREVO_TIMEOUT_SECONDS=10
```

Do not paste a real API key into `.env.example`, source control, frontend code, browser environment variables, issue descriptions, or logs. If a key is exposed, revoke it in Brevo and create a replacement.

Docker Compose reads the complete backend environment file, so no Compose YAML change is required. Restart the backend after changing environment values:

```sh
docker compose --env-file backend/.env -f compose.yaml -f compose.dev.yaml up -d --build --wait backend
```

For a direct local run, stop and restart Uvicorn.

## 3. Test the integration

Use the normal authentication flow rather than placing an API key in a shell command:

```sh
curl -i \
  -X POST http://localhost:8000/api/v1/auth/otp/request \
  -H 'Content-Type: application/json' \
  --data '{"email":"your-inbox@example.com"}'
```

Expected API status: `202 Accepted`. Check the recipient inbox and Brevo's **Transactional → Logs** page. The email should be tagged `authentication`.

An application response of `503 Unable to send verification email` means the Brevo call failed or configuration is absent. Check backend logs and then verify:

- The API key is active and is an API key, not an SMTP key.
- `BREVO_SENDER_EMAIL` is a verified sender or belongs to an authenticated domain.
- Transactional sending is activated on the Brevo account.
- The account has sending quota available.
- The backend container can reach `https://api.brevo.com`.

## 4. Current application behavior

- OTP mail failure returns `503` and invalidates the newly created OTP challenge so an undelivered code cannot be used.
- Membership approval and rejection emails are best-effort. The in-app notification remains available if Brevo is temporarily unavailable.
- Both plain-text and basic escaped HTML bodies are sent.
- Brevo messages are tagged `authentication` or `notification` for filtering in transactional logs.
