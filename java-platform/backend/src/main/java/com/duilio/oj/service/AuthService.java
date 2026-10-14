package com.duilio.oj.service;

import java.time.*;
import java.util.*;
import java.security.SecureRandom;
import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.duilio.oj.common.*;
import com.duilio.oj.dto.Requests.*;
import com.duilio.oj.mapper.UserMapper;
import com.duilio.oj.model.User;
import com.duilio.oj.security.*;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Profile;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.data.redis.core.script.DefaultRedisScript;
import org.springframework.mail.SimpleMailMessage;
import org.springframework.mail.javamail.JavaMailSender;
import org.springframework.security.oauth2.jwt.*;
import org.springframework.security.oauth2.jose.jws.MacAlgorithm;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@Profile("!judge")
public class AuthService {
    private final UserMapper users;
    private final Passwords passwords;
    private final JwtEncoder encoder;
    private final StringRedisTemplate redis;
    private final JavaMailSender mail;
    private final AbuseService abuse;
    private final String from;
    private final SecureRandom random=new SecureRandom();
    public AuthService(UserMapper users,Passwords passwords,JwtEncoder encoder,StringRedisTemplate redis,
        JavaMailSender mail,AbuseService abuse,@Value("${oj.mail-from}") String from) {
        this.users=users; this.passwords=passwords; this.encoder=encoder; this.redis=redis;
        this.mail=mail; this.abuse=abuse; this.from=from;
    }
    public static String email(String value) { return value.trim().toLowerCase(Locale.ROOT); }
    public void sendCode(String value,String ip,String purpose) {
        String address=email(value);
        abuse.limit("mail-ip:"+ip,10,3600,0);
        abuse.limit("mail:"+purpose+":"+address,1,60,0);
        if(purpose.equals("reset")&&users.selectCount(new QueryWrapper<User>().eq("email",address))==0) return;
        if(purpose.equals("register")) ApiException.require(users.selectCount(new QueryWrapper<User>().eq("email",address))==0,409,"Email already registered");
        String code=String.format("%06d",random.nextInt(1000000));
        String key="oj:code:"+purpose+":"+address;
        redis.opsForValue().set(key,passwords.encode(code),Duration.ofMinutes(10));
        var message=new SimpleMailMessage();
        message.setFrom(from); message.setTo(address); message.setSubject("duilio OJ verification");
        message.setText("Your "+purpose+" code is "+code+". Valid for 10 minutes.");
        try { mail.send(message); }
        catch(Exception e) { redis.delete(key); throw new ApiException(503,"Email service unavailable"); }
    }
    private void verify(String address,String purpose,String code) {
        abuse.limit("code:"+purpose+":"+address,10,600,0);
        String key="oj:code:"+purpose+":"+address;
        String encoded=redis.opsForValue().get(key);
        ApiException.require(encoded!=null&&passwords.matches(code,encoded),400,"Invalid or expired verification code");
        Long consumed=redis.execute(new DefaultRedisScript<>("""
            if redis.call('GET',KEYS[1])==ARGV[1] then return redis.call('DEL',KEYS[1]) end
            return 0
            """,Long.class),List.of(key),encoded);
        ApiException.require(consumed!=null&&consumed==1,400,"Code already used");
    }
    public Map<String,Object> login(Login input,String ip) {
        abuse.limit("login-ip:"+ip,30,300,0);
        User user=users.selectOne(new QueryWrapper<User>().eq("username",input.username()));
        ApiException.require(user!=null&&Boolean.TRUE.equals(user.active)&&passwords.matches(input.password(),user.password),401,"Invalid username or password");
        if(user.password.startsWith("pbkdf2_sha256$")) user.password=passwords.encode(input.password());
        user.lastSeenAt=Instant.now(); users.updateById(user);
        return session(user);
    }
    @Transactional
    public Map<String,Object> register(Register input) {
        String address=email(input.email());
        ApiException.require(users.selectCount(new QueryWrapper<User>().eq("username",input.username()).or().eq("email",address))==0,409,"Username or email already registered");
        verify(address,"register",input.code());
        User user=new User(); user.username=input.username(); user.email=address; user.password=passwords.encode(input.password());
        user.role="MEMBER"; user.school=Objects.requireNonNullElse(input.school(),"");
        user.realName=Objects.requireNonNullElse(input.realName(),""); user.active=true; user.tokenVersion=0;
        user.createdAt=Instant.now(); user.lastSeenAt=user.createdAt; users.insert(user);
        return session(user);
    }
    @Transactional
    public void reset(PasswordReset input) {
        String address=email(input.email()); verify(address,"reset",input.code());
        User user=users.selectOne(new QueryWrapper<User>().eq("email",address));
        ApiException.require(user!=null,400,"Invalid reset request");
        user.password=passwords.encode(input.password()); user.tokenVersion++; users.updateById(user);
    }
    public Map<String,Object> session(User user) {
        Instant now=Instant.now();
        var claims=JwtClaimsSet.builder().issuer("duilio-oj").subject(user.id.toString()).issuedAt(now)
            .expiresAt(now.plusSeconds(7200)).claim("version",user.tokenVersion).id(UUID.randomUUID().toString()).build();
        String token=encoder.encode(JwtEncoderParameters.from(JwsHeader.with(MacAlgorithm.HS256).build(),claims)).getTokenValue();
        return Map.of("token",token,"user",privateView(user),"expires_in",7200);
    }
    public static Map<String,Object> publicView(User user) {
        return Map.of("id",user.id,"username",user.username,"role",user.role,"school",user.school,
            "is_online",user.lastSeenAt!=null&&user.lastSeenAt.isAfter(Instant.now().minusSeconds(300)));
    }
    public static Map<String,Object> privateView(User user) {
        var result=new LinkedHashMap<>(publicView(user));
        result.put("email",user.email); result.put("real_name",user.realName); result.put("active",user.active);
        return result;
    }
}

