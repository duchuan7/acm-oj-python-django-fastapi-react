package com.duilio.oj.model;

import com.baomidou.mybatisplus.annotation.*;

@TableName(value="problem_proposal", autoResultMap=true)
public class ProblemProposal {
    @TableId(type=IdType.AUTO)
    public Long id;
    public Long authorId;
    public String title;
    public String problemData;
    public String standardLanguage;
    public String standardCode;
    public String status;
    public String reviewMessage;
    public Long reviewedBy;
    public Long approvedProblem;
    public java.time.Instant createdAt;
    public java.time.Instant reviewedAt;
}

