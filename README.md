# ACM Training Online Judge

An online judge system for ACM/ICPC training teams.

## Tech Stack

- Backend: Django + Django REST Framework
- Frontend: React + Ant Design + Vite
- Database: PostgreSQL
- Queue/cache: Redis
- Judge: Python worker + Docker SDK
- Sandbox: one Docker container per compile/run, with network disabled and CPU, memory, time, process, and capability limits

## Features

- User roles: admin, coach, member
- Login and registration
- Public problem browsing
- Problem management for admin/coach
- Problem proposal workflow: users submit statements and standard solutions, admin/coach review them
- Online submissions for C, C++, Java, and Python
- Judge verdicts: AC, Wrong Answer, Time Limit Exceeded, Memory Limit Exceeded, Compile Error, Runtime Error, System Error
- Submission history and per-testcase details
- Contest models for ACM/IOI style ranking
- Blog system
- User profile page with submissions and blog posts
- Chinese/English UI switch

## Directory

```text
.
|-- docker-compose.yml
|-- docker-compose.prod.yml
|-- .env.example
|-- .env.prod.example
|-- backend/
|   |-- apps/
|   |-- config/
|   |-- manage.py
|   `-- scripts/createsuperuser.sh
|-- frontend/
|   `-- src/
|-- judge/
|   |-- sandbox.py
|   |-- sandbox_pseudocode.py
|   `-- worker.py
`-- nginx/
```

## Local Run

Install and start Docker Desktop first.

```bash
cp .env.example .env
docker compose up --build
```

Open:

- Frontend: http://localhost:5173
- API root: http://localhost:8000/api/
- Django Admin: http://localhost:8000/admin/

Demo admin credentials are read from `.env.example` in local Docker Compose. Change them before using this outside local development.

You can also create an admin manually:

```bash
docker compose exec backend sh scripts/createsuperuser.sh
```

## Judge Notes

The judge worker creates temporary Docker containers for compile/run tasks and applies:

- disabled network
- memory limit
- CPU quota
- process limit
- dropped Linux capabilities
- no-new-privileges
- read-only testcase volume
- isolated run volume

This project is suitable as a training-team MVP. Before production use, further hardening is recommended, including dedicated judge nodes, seccomp profiles, image allowlists, special judge support, better testcase management, observability, and backup workflows.
