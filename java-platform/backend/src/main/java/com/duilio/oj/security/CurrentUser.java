package com.duilio.oj.security;

import com.duilio.oj.mapper.UserMapper;
import com.duilio.oj.model.User;
import com.duilio.oj.common.ApiException;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.oauth2.server.resource.authentication.JwtAuthenticationToken;
import org.springframework.stereotype.Component;

@Component
public class CurrentUser {
    private final UserMapper users;
    public CurrentUser(UserMapper users) { this.users=users; }
    public User optional() {
        var auth=SecurityContextHolder.getContext().getAuthentication();
        return auth instanceof JwtAuthenticationToken jwt ? users.selectById(Long.parseLong(jwt.getName())) : null;
    }
    public User required() { User user=optional(); ApiException.require(user!=null,401,"Please sign in"); return user; }
    public static boolean staff(User user) { return user!=null && ("ADMIN".equals(user.role)||"COACH".equals(user.role)); }
    public static boolean admin(User user) { return user!=null && "ADMIN".equals(user.role); }
    public User requireStaff() { User user=required(); ApiException.require(staff(user),403,"Coach or admin required"); return user; }
    public User requireAdmin() { User user=required(); ApiException.require(admin(user),403,"Admin required"); return user; }
}

