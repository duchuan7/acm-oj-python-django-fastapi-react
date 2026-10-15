package com.duilio.oj.config;

import org.springframework.amqp.core.*;
import org.springframework.context.annotation.*;

@Configuration
public class QueueConfig {
    public static final String QUEUE = "oj.judge.v1";

    @Bean
    Queue judgeQueue() {
        return QueueBuilder.durable(QUEUE)
                .deadLetterExchange("oj.dead")
                .deadLetterRoutingKey("dead")
                .build();
    }

    @Bean
    Queue deadQueue() {
        return QueueBuilder.durable("oj.judge.dead").build();
    }

    @Bean
    DirectExchange deadExchange() {
        return new DirectExchange("oj.dead");
    }

    @Bean
    Binding deadBinding() {
        return BindingBuilder.bind(deadQueue()).to(deadExchange()).with("dead");
    }
}
