package com.duilio.oj.model;

import com.baomidou.mybatisplus.annotation.*;

@TableName(value="problem_solution", autoResultMap=true)
public class ProblemSolution {
    @TableId(type=IdType.AUTO)
    public Long id;
    public Long problemId;
    public Long authorId;
    public String title;
    public String content;
    public String status;
    public String reviewMessage;
    public Long reviewedBy;
    public java.time.Instant createdAt;
    public java.time.Instant reviewedAt;
    public java.time.Instant updatedAt;
}

