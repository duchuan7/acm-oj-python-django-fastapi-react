package com.duilio.oj.model;

import com.baomidou.mybatisplus.annotation.*;

@TableName(value = "submission", autoResultMap = true)
public class Submission {
    @TableId(type = IdType.AUTO)
    public Long id;

    public Long userId;
    public Long problemId;
    public Long contestId;
    public String language;
    @com.fasterxml.jackson.annotation.JsonIgnore public String code;
    public Integer codeSize;
    public String verdict;
    public Integer score;
    public Integer maxTimeMs;
    public Integer maxMemoryKb;
    public String compileMessage;
    public java.time.Instant submittedAt;
    public java.time.Instant judgedAt;
    public String leaseToken;
    public java.time.Instant leaseUntil;
    public Integer judgeAttempts;
}
