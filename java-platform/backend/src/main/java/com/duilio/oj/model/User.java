package com.duilio.oj.model;

import com.baomidou.mybatisplus.annotation.*;

@TableName(value = "oj_user", autoResultMap = true)
public class User {
    @TableId(type = IdType.AUTO)
    public Long id;

    public String username;
    public String email;
    @com.fasterxml.jackson.annotation.JsonIgnore public String password;
    public String role;
    public String school;
    public String realName;
    public Boolean active;
    public Integer tokenVersion;
    public java.time.Instant lastSeenAt;
    public java.time.Instant createdAt;
}
