package com.duilio.oj.mapper;

import org.apache.ibatis.annotations.*;

import java.util.*;

public interface StatisticsMapper {
    @Select(
            """
            SELECT COUNT(*) AS submission_count,COUNT(DISTINCT CASE WHEN s.verdict='ACCEPTED' THEN s.problem_id END) AS solved_count
            FROM submission s JOIN problem p ON p.id=s.problem_id WHERE s.user_id=#{id} AND p.is_public=TRUE
            """)
    Map<String, Object> userStats(Long id);

    @Select(
            """
            SELECT s.id,s.problem_id,p.title AS problem_title,s.language,s.verdict,s.score,s.submitted_at
            FROM submission s JOIN problem p ON p.id=s.problem_id WHERE s.user_id=#{id} AND p.is_public=TRUE ORDER BY s.id DESC LIMIT 50
            """)
    List<Map<String, Object>> profileSubmissions(Long id);

    @Select(
            """
            SELECT u.id AS user_id,u.username,COUNT(DISTINCT CASE WHEN s.verdict='ACCEPTED' THEN s.problem_id END) AS solved_count,
            COUNT(s.id) AS submission_count FROM oj_user u JOIN submission s ON s.user_id=u.id
            JOIN problem p ON p.id=s.problem_id WHERE p.is_public=TRUE AND u.active=TRUE
            GROUP BY u.id,u.username ORDER BY solved_count DESC,submission_count,u.username LIMIT 10
            """)
    List<Map<String, Object>> leaderboard();

    @Select(
            """
            SELECT COUNT(*) AS submission_count,SUM(CASE WHEN verdict='ACCEPTED' THEN 1 ELSE 0 END) AS accepted_count
            FROM submission WHERE problem_id=#{id}
            """)
    Map<String, Object> problemStats(Long id);
}
