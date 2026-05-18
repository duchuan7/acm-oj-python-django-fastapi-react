# Production Deployment

This document describes a generic HTTP deployment using Docker Compose, PostgreSQL, Redis, Nginx, the Django backend, the React frontend, and the judge worker.

## 1. Server Requirements

Recommended minimum server:

- 2 CPU cores
- 4 GB RAM
- 40 GB disk
- Ubuntu 22.04 or 24.04
- Open ports: `22`, `80`, and later `443` for HTTPS

## 2. DNS

Create DNS records for your own domain:

```text
Host: @
Type: A
Value: your-server-public-ip

Host: www
Type: A
Value: your-server-public-ip
```

DNS propagation can take from a few minutes to several hours.

## 3. Install Docker

On the server:

```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
```

Log out and log in again, then check:

```bash
docker --version
docker compose version
```

## 4. Configure Environment

Copy the example production environment:

```bash
cp .env.prod.example .env.prod
nano .env.prod
```

At minimum, change:

```text
DJANGO_SECRET_KEY
POSTGRES_PASSWORD
JUDGE_INTERNAL_TOKEN
DEMO_ADMIN_PASSWORD
DJANGO_ALLOWED_HOSTS
CSRF_TRUSTED_ORIGINS
CORS_ALLOWED_ORIGINS
```

Also update `nginx/default.conf` and replace `example.com` with your real domain.

## 5. Start Services

```bash
docker compose -f docker-compose.prod.yml --env-file .env.prod up --build -d
```

Check status:

```bash
docker compose -f docker-compose.prod.yml --env-file .env.prod ps
```

View logs:

```bash
docker compose -f docker-compose.prod.yml --env-file .env.prod logs -f backend
docker compose -f docker-compose.prod.yml --env-file .env.prod logs -f judge
```

## 6. HTTPS

After confirming HTTP works, enable HTTPS with one of:

- Caddy automatic HTTPS
- Nginx + Certbot
- cloud provider certificate service

When HTTPS is enabled, update `.env.prod`:

```text
CSRF_TRUSTED_ORIGINS=https://example.com,https://www.example.com
CORS_ALLOWED_ORIGINS=https://example.com,https://www.example.com
```

Replace `example.com` with your real domain.
