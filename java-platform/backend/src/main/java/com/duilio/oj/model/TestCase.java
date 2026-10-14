package com.duilio.oj.model;

import com.baomidou.mybatisplus.annotation.*;

@TableName(value="test_case", autoResultMap=true)
public class TestCase {
    @TableId(type=IdType.AUTO)
    public Long id;
    public Long problemId;
    public Integer caseOrder;
    public String inputText;
    public String outputText;
    public Integer score;
    public Boolean isSample;
}

