CREATE TABLE oj_user (
 id BIGINT PRIMARY KEY AUTO_INCREMENT, username VARCHAR(150) NOT NULL UNIQUE, email VARCHAR(254) UNIQUE,
 password VARCHAR(256) NOT NULL, role VARCHAR(16) NOT NULL DEFAULT 'MEMBER', school VARCHAR(128) NOT NULL DEFAULT '',
 real_name VARCHAR(64) NOT NULL DEFAULT '', active BOOLEAN NOT NULL DEFAULT TRUE, token_version INT NOT NULL DEFAULT 0,
 last_seen_at DATETIME(6), created_at DATETIME(6) NOT NULL
);
CREATE TABLE problem (
 id BIGINT PRIMARY KEY AUTO_INCREMENT, title VARCHAR(200) NOT NULL, slug VARCHAR(220) NOT NULL UNIQUE,
 description LONGTEXT NOT NULL, input_description LONGTEXT NOT NULL, output_description LONGTEXT NOT NULL,
 samples LONGTEXT NOT NULL, time_limit_ms INT NOT NULL, memory_limit_mb INT NOT NULL, difficulty INT,
 tags LONGTEXT NOT NULL, source VARCHAR(200) NOT NULL DEFAULT '', is_public BOOLEAN NOT NULL DEFAULT FALSE,
 created_by BIGINT NOT NULL, created_at DATETIME(6) NOT NULL, updated_at DATETIME(6) NOT NULL,
 FOREIGN KEY (created_by) REFERENCES oj_user(id)
);
CREATE TABLE test_case (
 id BIGINT PRIMARY KEY AUTO_INCREMENT, problem_id BIGINT NOT NULL, case_order INT NOT NULL,
 input_text LONGTEXT NOT NULL, output_text LONGTEXT NOT NULL, score INT NOT NULL DEFAULT 0,
 is_sample BOOLEAN NOT NULL DEFAULT FALSE, UNIQUE (problem_id,case_order), FOREIGN KEY(problem_id) REFERENCES problem(id)
);
CREATE TABLE contest (
 id BIGINT PRIMARY KEY AUTO_INCREMENT, title VARCHAR(200) NOT NULL, description LONGTEXT NOT NULL,
 rule VARCHAR(8) NOT NULL, start_at DATETIME(6) NOT NULL, end_at DATETIME(6) NOT NULL,
 is_public BOOLEAN NOT NULL, freeze_rank_minutes INT NOT NULL DEFAULT 0, created_by BIGINT NOT NULL,
 created_at DATETIME(6) NOT NULL, FOREIGN KEY(created_by) REFERENCES oj_user(id)
);
CREATE TABLE contest_participant (
 id BIGINT PRIMARY KEY AUTO_INCREMENT, contest_id BIGINT NOT NULL, user_id BIGINT NOT NULL,
 UNIQUE(contest_id,user_id), FOREIGN KEY(contest_id) REFERENCES contest(id), FOREIGN KEY(user_id) REFERENCES oj_user(id)
);
CREATE TABLE contest_problem (
 id BIGINT PRIMARY KEY AUTO_INCREMENT, contest_id BIGINT NOT NULL, problem_id BIGINT NOT NULL,
 alias VARCHAR(8) NOT NULL, score INT NOT NULL, problem_order INT NOT NULL, created_for_contest BOOLEAN NOT NULL,
 UNIQUE(contest_id,problem_id), UNIQUE(contest_id,alias), FOREIGN KEY(contest_id) REFERENCES contest(id),
 FOREIGN KEY(problem_id) REFERENCES problem(id)
);
CREATE TABLE submission (
 id BIGINT PRIMARY KEY AUTO_INCREMENT, user_id BIGINT NOT NULL, problem_id BIGINT NOT NULL, contest_id BIGINT,
 language VARCHAR(16) NOT NULL, code LONGTEXT NOT NULL, code_size INT NOT NULL, verdict VARCHAR(32) NOT NULL,
 score INT NOT NULL DEFAULT 0, max_time_ms INT NOT NULL DEFAULT 0, max_memory_kb INT NOT NULL DEFAULT 0,
 compile_message LONGTEXT NOT NULL, submitted_at DATETIME(6) NOT NULL, judged_at DATETIME(6),
 lease_token VARCHAR(64), lease_until DATETIME(6), judge_attempts INT NOT NULL DEFAULT 0,
 FOREIGN KEY(user_id) REFERENCES oj_user(id), FOREIGN KEY(problem_id) REFERENCES problem(id),
 FOREIGN KEY(contest_id) REFERENCES contest(id)
);
CREATE INDEX submission_user_time ON submission(user_id,submitted_at);
CREATE INDEX submission_problem_verdict ON submission(problem_id,verdict);
CREATE INDEX submission_contest_user ON submission(contest_id,user_id);
CREATE TABLE case_result (
 id BIGINT PRIMARY KEY AUTO_INCREMENT, submission_id BIGINT NOT NULL, case_id BIGINT NOT NULL, status VARCHAR(32) NOT NULL,
 time_used INT NOT NULL, memory_used INT NOT NULL, exit_code INT, stdout LONGTEXT NOT NULL, stderr LONGTEXT NOT NULL,
 score INT NOT NULL, UNIQUE(submission_id,case_id), FOREIGN KEY(submission_id) REFERENCES submission(id),
 FOREIGN KEY(case_id) REFERENCES test_case(id)
);
CREATE TABLE judge_outbox (
 id BIGINT PRIMARY KEY AUTO_INCREMENT, submission_id BIGINT NOT NULL, sent_at DATETIME(6), created_at DATETIME(6) NOT NULL,
 FOREIGN KEY(submission_id) REFERENCES submission(id)
);
CREATE INDEX outbox_unsent ON judge_outbox(sent_at,id);
CREATE TABLE problem_proposal (
 id BIGINT PRIMARY KEY AUTO_INCREMENT, author_id BIGINT NOT NULL, title VARCHAR(200) NOT NULL,
 problem_data LONGTEXT NOT NULL, standard_language VARCHAR(16) NOT NULL, standard_code LONGTEXT NOT NULL,
 status VARCHAR(16) NOT NULL, review_message LONGTEXT NOT NULL, reviewed_by BIGINT, approved_problem BIGINT,
 created_at DATETIME(6) NOT NULL, reviewed_at DATETIME(6), FOREIGN KEY(author_id) REFERENCES oj_user(id),
 FOREIGN KEY(reviewed_by) REFERENCES oj_user(id), FOREIGN KEY(approved_problem) REFERENCES problem(id)
);
CREATE TABLE problem_solution (
 id BIGINT PRIMARY KEY AUTO_INCREMENT, problem_id BIGINT NOT NULL, author_id BIGINT NOT NULL, title VARCHAR(200) NOT NULL,
 content LONGTEXT NOT NULL, status VARCHAR(16) NOT NULL, review_message LONGTEXT NOT NULL, reviewed_by BIGINT,
 created_at DATETIME(6) NOT NULL, reviewed_at DATETIME(6), updated_at DATETIME(6) NOT NULL,
 FOREIGN KEY(problem_id) REFERENCES problem(id), FOREIGN KEY(author_id) REFERENCES oj_user(id),
 FOREIGN KEY(reviewed_by) REFERENCES oj_user(id)
);
CREATE TABLE blog_post (
 id BIGINT PRIMARY KEY AUTO_INCREMENT, author_id BIGINT NOT NULL, title VARCHAR(200) NOT NULL, content LONGTEXT NOT NULL,
 status VARCHAR(16) NOT NULL, created_at DATETIME(6) NOT NULL, updated_at DATETIME(6) NOT NULL,
 FOREIGN KEY(author_id) REFERENCES oj_user(id)
);

