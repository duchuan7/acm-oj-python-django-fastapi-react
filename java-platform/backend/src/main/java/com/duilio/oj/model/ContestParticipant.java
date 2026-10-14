package com.duilio.oj.model;

import com.baomidou.mybatisplus.annotation.*;

@TableName(value="contest_participant", autoResultMap=true)
public class ContestParticipant {
    @TableId(type=IdType.AUTO)
    public Long id;
    public Long contestId;
    public Long userId;
}

