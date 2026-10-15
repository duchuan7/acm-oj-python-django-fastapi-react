package com.duilio.oj.model;

import com.baomidou.mybatisplus.annotation.*;

@TableName(value = "blog_post", autoResultMap = true)
public class BlogPost {
    @TableId(type = IdType.AUTO)
    public Long id;

    public Long authorId;
    public String title;
    public String content;
    public String status;
    public java.time.Instant createdAt;
    public java.time.Instant updatedAt;
}
