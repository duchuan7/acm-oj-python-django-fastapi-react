package com.duilio.oj;

import org.apache.ibatis.executor.statement.StatementHandler;
import org.apache.ibatis.plugin.*;
import org.springframework.boot.test.context.TestConfiguration;
import org.springframework.context.annotation.Bean;

import java.sql.Connection;
import java.util.*;

@TestConfiguration
class SqlQueryCounter {
    @Bean
    Counter sqlQueryCounter() {
        return new Counter();
    }

    @Intercepts(
            @Signature(
                    type = StatementHandler.class,
                    method = "prepare",
                    args = {Connection.class, Integer.class}))
    static class Counter implements Interceptor {
        private final ThreadLocal<List<String>> queries = new ThreadLocal<>();

        void start() {
            queries.set(new ArrayList<>());
        }

        List<String> stop() {
            var captured = List.copyOf(queries.get());
            queries.remove();
            return captured;
        }

        @Override
        public Object intercept(Invocation invocation) throws Throwable {
            var captured = queries.get();
            String sql = ((StatementHandler) invocation.getTarget()).getBoundSql().getSql();
            if (captured != null && sql.stripLeading().regionMatches(true, 0, "SELECT", 0, 6))
                captured.add(sql);
            return invocation.proceed();
        }
    }
}
