package com.duilio.oj.model;

import com.baomidou.mybatisplus.annotation.*;

@TableName(value="contest_problem", autoResultMap=true)
public class ContestProblem {
    @TableId(type=IdType.AUTO)
    public Long id;
    public Long contestId;
    public Long problemId;
    public String alias;
    public Integer score;
    public Integer problemOrder;
    public Boolean createdForContest;
}

