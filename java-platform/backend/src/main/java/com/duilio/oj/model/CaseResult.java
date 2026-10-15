package com.duilio.oj.model;

import com.baomidou.mybatisplus.annotation.*;

@TableName(value = "case_result", autoResultMap = true)
public class CaseResult {
    @TableId(type = IdType.AUTO)
    public Long id;

    public Long submissionId;
    public Long caseId;
    public String status;
    public Integer timeUsed;
    public Integer memoryUsed;
    public Integer exitCode;
    public String stdout;
    public String stderr;
    public Integer score;
    public String message;
    public java.time.Instant createdAt;
}
