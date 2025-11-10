package com.jiaxin.zhupicture.exception;

import com.jiaxin.zhupicture.common.BaseResponse;
import com.jiaxin.zhupicture.common.ResultUtils;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.ControllerAdvice;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

/**
 * 全局异常处理器
 * 当出现无法控制的报错，则通过封装返回好看的异常
 */
@RestControllerAdvice//@ControllerAdvice只负责拦截异常；要想把你返回的 BaseResponse 序列化成 JSON 并写回给浏览器，还必须让 Spring MVC 认为“这是一个 @ResponseBody 的结果” 所以需要改为@RestControllerAdvice。
@Slf4j
public class GlobalExceptionHandler {

    @ExceptionHandler(BusinessException.class)
    public BaseResponse<?> businessExceptionHandler(BusinessException e) {
        log.error("BusinessException", e);
        return ResultUtils.error(e.getCode(), e.getMessage());
    }

    @ExceptionHandler(RuntimeException.class)
    public BaseResponse<?> businessExceptionHandler(RuntimeException e) {
        log.error("RuntimeException", e);
        return ResultUtils.error(ErrorCode.SYSTEM_ERROR, "系统错误");
    }

}
