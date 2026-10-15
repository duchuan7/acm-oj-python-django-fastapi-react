package com.duilio.oj.service;

import com.duilio.oj.common.ApiException;

import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.data.redis.core.script.DefaultRedisScript;
import org.springframework.stereotype.Service;

import java.util.*;

@Service
public class AbuseService {
    private final StringRedisTemplate redis;

    public AbuseService(StringRedisTemplate redis) {
        this.redis = redis;
    }

    private static final DefaultRedisScript<Long> LIMIT =
            new DefaultRedisScript<>(
                    """
                    local t=redis.call('TIME')
                    local now=t[1]*1000+math.floor(t[2]/1000)
                    local window=tonumber(ARGV[1])
                    redis.call('ZREMRANGEBYSCORE',KEYS[1],'-inf',now-window)
                    local last=redis.call('ZREVRANGE',KEYS[1],0,0,'WITHSCORES')
                    if #last>0 and now-tonumber(last[2])<tonumber(ARGV[3]) then return 1 end
                    if redis.call('ZCARD',KEYS[1])>=tonumber(ARGV[2]) then return 1 end
                    redis.call('ZADD',KEYS[1],now,ARGV[4])
                    redis.call('PEXPIRE',KEYS[1],window)
                    return 0
                    """,
                    Long.class);

    public void limit(String key, int count, int seconds, int gapMs) {
        Long denied =
                redis.execute(
                        LIMIT,
                        List.of("oj:rate:" + key),
                        "" + (seconds * 1000),
                        "" + count,
                        "" + gapMs,
                        UUID.randomUUID().toString());
        ApiException.require(denied != null && denied == 0, 429, "Too many requests; please wait");
    }
}
