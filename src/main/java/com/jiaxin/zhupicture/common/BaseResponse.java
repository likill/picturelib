package com.jiaxin.zhupicture.common;

import com.jiaxin.zhupicture.exception.ErrorCode;
import lombok.Data;

import java.io.Serializable;

/**
 * 接口返回值封装类
 */
//
@Data
public class BaseResponse<T> implements Serializable {
    private int code;
    private String msg;
    private T data;
    public BaseResponse(int code, String msg, T data) {
        this.code = code;
        this.msg = msg;
        this.data = data;
    }
    public BaseResponse(int code, T data) {
        this(code, "", data);
    }
    public BaseResponse(ErrorCode errorCode) {
        this(errorCode.getCode(),errorCode.getMessage(),null);
    }

}
