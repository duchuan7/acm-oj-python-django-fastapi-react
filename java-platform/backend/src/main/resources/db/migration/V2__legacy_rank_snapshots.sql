CREATE TABLE contest_rank_snapshot (
 id BIGINT PRIMARY KEY AUTO_INCREMENT, contest_id BIGINT NOT NULL, generated_at DATETIME(6) NOT NULL,
 frozen BOOLEAN NOT NULL, payload LONGTEXT NOT NULL, FOREIGN KEY(contest_id) REFERENCES contest(id)
);

