# Private client file intake service

This API receives customer project files for Software QA Lab. It is designed to run separately from GitHub Pages. Uploaded files and the SQLite database are stored under the persistent `DATA_DIR` (default `/data`), never in the public website directory or Git repository.

## Deploy

1. Deploy this directory as a Docker service on a trusted host that supports persistent volumes and HTTPS.
2. Mount a persistent private volume at `/data`.
3. Set `ADMIN_TOKEN` to a long random secret (at least 32 random bytes). Keep it in the host's secret manager; never commit it.
4. Set `ALLOWED_ORIGINS` to the exact GitHub Pages origin shown in `.env.example`.
5. Expose the service only through HTTPS. Do not expose the private volume or SQLite file.
6. Set `MAX_FILE_BYTES` as required (default 20 MiB). Confirm the host/reverse-proxy request-body limit is at least this value plus multipart overhead.
7. After deployment, set `window.SOFTWARE_QA_INTAKE_API` in `docs/intake-config.js` to the HTTPS API origin. The form stays disabled until a real API origin is configured.

Example local run (requires Docker):

```powershell
Copy-Item .env.example .env
# Edit .env and replace ADMIN_TOKEN with a long random secret.
docker build -t software-qa-intake .
docker run --rm -p 8000:8000 --env-file .env -v qa-intake-data:/data software-qa-intake
```

Health check: `GET /health`.

## Private admin API

Send the admin token in an Authorization header:

- `GET /api/admin/submissions` lists up to 200 submissions.
- `GET /api/admin/submissions/{id}/file` downloads a file.
- `DELETE /api/admin/submissions/{id}` deletes a submission and its file.

Do not put the admin token in the website, JavaScript, GitHub Pages, a public issue, or a customer-facing link. Use a private admin tool or an authenticated server-side client.

## Security controls and limits

- Uploads are limited to 20 MiB by default, five per source IP per rolling hour (in-memory), and an allowlist of APK/AAB/ZIP/PDF/PNG/JPEG/TXT/JSON/CSV extensions.
- Known binary file signatures are checked; JSON must parse; text must be UTF-8. MIME headers and file extensions alone are not trusted.
- Files get random server-side names, are never extracted or executed, and are stored outside the public web root.
- No public file URLs exist. Listing, downloading, and deletion require the admin bearer token.
- CORS is restricted to the configured site origin. CORS is not authentication.
- The rate limit is in-memory and resets on restart; a production deployment should add reverse-proxy rate limiting, malware scanning, monitoring, encrypted backups, retention/deletion policy, and a secure admin interface.
- The service does not scan APKs or archives for malware. Never install or execute customer files on a personal device; use an isolated test environment.
- Collect only the minimum personal data needed. Define a retention period and privacy notice before accepting real customer data.
- Do not upload credentials, production customer databases, private keys, wallet seed phrases, or data the customer is not authorized to share.
- Run behind HTTPS. Do not use this service for unlawful or unauthorized files or testing.

This service is an implementation starter, not a completed security certification or a substitute for operational hardening.
