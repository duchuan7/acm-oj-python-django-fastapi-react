package com.duilio.oj.model;

import com.baomidou.mybatisplus.annotation.*;

@TableName(value="contest", autoResultMap=true)
public class Contest {
    @TableId(type=IdType.AUTO)
    public Long id;
    public String title;
    public String description;
    public String rule;
    public java.time.Instant startAt;
    public java.time.Instant endAt;
    public Boolean isPublic;
    public Integer freezeRankMinutes;
    public Long createdBy;
    public java.time.Instant createdAt;
}

