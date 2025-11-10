package com.jiaxin.zhupicture.aop;

import com.jiaxin.zhupicture.annotation.AuthCheck;
import com.jiaxin.zhupicture.exception.BusinessException;
import com.jiaxin.zhupicture.exception.ErrorCode;
import com.jiaxin.zhupicture.model.entity.User;
import com.jiaxin.zhupicture.model.enums.UserRoleEnum;
import com.jiaxin.zhupicture.service.UserService;
import org.aspectj.lang.ProceedingJoinPoint;
import org.aspectj.lang.annotation.Around;
import org.aspectj.lang.annotation.Aspect;
import org.springframework.stereotype.Component;
import org.springframework.web.context.request.RequestAttributes;
import org.springframework.web.context.request.RequestContextHolder;
import org.springframework.web.context.request.ServletRequestAttributes;

import javax.annotation.Resource;
import javax.servlet.http.HttpServletRequest;

@Aspect
@Component
public class AuthInterceptor {
    @Resource
    private UserService userService;
    //jionPoint
    /**
     * 执行拦截
     * @param joinPoint
     * @param authcheck
     * @return
     * @throws Throwable
     */

    @Around("@annotation(authcheck)")//环绕切面：定义切面的执行时间，这个表示前后都要进行检测
    public Object doInterceptor(ProceedingJoinPoint joinPoint, AuthCheck authcheck) throws Throwable {
        String mustRole =  authcheck.mustRole();
        RequestAttributes requestAttributes = RequestContextHolder.getRequestAttributes();
        HttpServletRequest request = ((ServletRequestAttributes) requestAttributes).getRequest();
        //获取当前登录用户
        User loginUser = userService.getLoginUser(request);
        UserRoleEnum mustRoleEnum = UserRoleEnum.getEnumByValue(mustRole);
        //如果不需要权限放行
        if(mustRoleEnum==null){
            return joinPoint.proceed();
        }
        UserRoleEnum userRoleEnum = UserRoleEnum.getEnumByValue(loginUser.getUserRole());
        if (userRoleEnum == null) {
            throw new BusinessException(ErrorCode.NO_AUTH_ERROR);
        }
        // 要求必须有管理员权限，但用户没有管理员权限，拒绝
        if (UserRoleEnum.ADMIN.equals(mustRoleEnum) && !UserRoleEnum.ADMIN.equals(userRoleEnum)) {
            throw new BusinessException(ErrorCode.NO_AUTH_ERROR);
        }
        return joinPoint.proceed();
    }
}
