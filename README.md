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
- Problem editorial workflow: users write problem editorials, admin/coach approve or reject them in a review queue
- Online submissions for C, C++, Java, and Python
- Judge statuses: Pending, Judging, Accepted, Wrong Answer, Time Limit Exceeded, Memory Limit Exceeded, Runtime Error, Compile Error, Output Limit Exceeded, System Error
- Submission history, submission detail API, and per-testcase results
- Contest system with public contests, private contests, ACM/IOI rules, problemset picks, contest-only new problems, and ranklists
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

The judge flow is:

```text
User submits code
-> backend creates a Submission with PENDING status
-> backend pushes the submission id into Redis
-> judge worker consumes the queue item
-> backend marks the submission as JUDGING
-> judge worker compiles in a Docker sandbox when needed
-> judge worker runs each testcase independently in Docker
-> backend stores one submission_case_result row per testcase
-> backend updates the final Submission status
```

Final status rules:

- Compile failure: `COMPILE_ERROR`
- First failed testcase decides the final status: `WRONG_ANSWER`, `TIME_LIMIT_EXCEEDED`, `MEMORY_LIMIT_EXCEEDED`, `RUNTIME_ERROR`, or `OUTPUT_LIMIT_EXCEEDED`
- All testcases accepted: `ACCEPTED`
- Unexpected judge/backend error: `SYSTEM_ERROR`

The `submission_case_result` table stores:

- submission
- case
- status
- time_used
- memory_used
- exit_code
- stdout
- stderr
- created_at

The judge worker creates temporary Docker containers for compile/run tasks and applies:

- disabled network
- memory limit
- CPU quota
- process limit
- run timeout
- dropped Linux capabilities
- no-new-privileges
- read-only testcase volume
- isolated run volume
- automatic container removal
- temporary directory cleanup

Submission API:

```text
GET /api/submissions/
GET /api/submissions/?problem=1
GET /api/submissions/?language=CPP
GET /api/submissions/?status=ACCEPTED
GET /api/submissions/{id}/
```

Editorial API:

```text
GET /api/problem-solutions/
GET /api/problem-solutions/?problem=1
GET /api/problem-solutions/?status=PENDING
POST /api/problem-solutions/
POST /api/problem-solutions/{id}/approve/
POST /api/problem-solutions/{id}/reject/
```

## Contest Notes

Contest APIs:

```text
GET /api/contests/
GET /api/contests/?visibility=public
GET /api/contests/?visibility=private
POST /api/contests/
GET /api/contests/{id}/ranklist/
```

Rules:

- Public contests can only be created by admins.
- Private contests can be created by any logged-in user.
- Contest problems can reference existing public problems from the problemset.
- Contest creators can also create a new problem directly inside the contest.
- New contest-only problems are hidden from the public problemset while the contest is running.
- When a contest has ended, contest-created problems are automatically marked public the next time the contest API is read.

This project is suitable as a training-team MVP. Before production use, further hardening is recommended, including dedicated judge nodes, seccomp profiles, image allowlists, special judge support, better testcase management, observability, and backup workflows.
