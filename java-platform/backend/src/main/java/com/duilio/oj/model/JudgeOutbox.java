package com.duilio.oj.model;

import com.baomidou.mybatisplus.annotation.*;

@TableName(value="judge_outbox", autoResultMap=true)
public class JudgeOutbox {
    @TableId(type=IdType.AUTO)
    public Long id;
    public Long submissionId;
    public java.time.Instant sentAt;
    public java.time.Instant createdAt;
}

