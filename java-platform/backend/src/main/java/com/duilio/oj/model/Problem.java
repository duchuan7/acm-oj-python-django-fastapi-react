package com.duilio.oj.model;

import com.baomidou.mybatisplus.annotation.*;

@TableName(value = "problem", autoResultMap = true)
public class Problem {
    @TableId(type = IdType.AUTO)
    public Long id;

    public String title;
    public String slug;
    public String description;
    public String inputDescription;
    public String outputDescription;

    @com.baomidou.mybatisplus.annotation.TableField(
            typeHandler = com.baomidou.mybatisplus.extension.handlers.JacksonTypeHandler.class)
    public java.util.List<java.util.Map<String, String>> samples;

    public Integer timeLimitMs;
    public Integer memoryLimitMb;
    public Integer difficulty;

    @com.baomidou.mybatisplus.annotation.TableField(
            typeHandler = com.baomidou.mybatisplus.extension.handlers.JacksonTypeHandler.class)
    public java.util.List<String> tags;

    public String source;
    public Boolean isPublic;
    public Long createdBy;
    public java.time.Instant createdAt;
    public java.time.Instant updatedAt;
}
