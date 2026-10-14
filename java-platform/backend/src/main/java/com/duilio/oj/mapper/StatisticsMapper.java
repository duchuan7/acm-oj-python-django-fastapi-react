package com.duilio.oj.mapper;

import java.util.*;
import org.apache.ibatis.annotations.*;

public interface StatisticsMapper {
    @Select("""
        SELECT u.id AS user_id,u.username,COUNT(DISTINCT CASE WHEN s.verdict='ACCEPTED' THEN s.problem_id END) AS solved_count,
        COUNT(s.id) AS submission_count FROM oj_user u JOIN submission s ON s.user_id=u.id
        JOIN problem p ON p.id=s.problem_id WHERE p.is_public=TRUE AND u.active=TRUE
        GROUP BY u.id,u.username ORDER BY solved_count DESC,submission_count,u.username LIMIT 10
        """)
    List<Map<String,Object>> leaderboard();
    @Select("""
        SELECT COUNT(*) AS submission_count,SUM(CASE WHEN verdict='ACCEPTED' THEN 1 ELSE 0 END) AS accepted_count
        FROM submission WHERE problem_id=#{id}
        """)
    Map<String,Object> problemStats(Long id);
}

