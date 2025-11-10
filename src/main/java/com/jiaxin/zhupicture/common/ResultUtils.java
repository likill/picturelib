package com.jiaxin.zhupicture.common;

import com.jiaxin.zhupicture.exception.ErrorCode;

/**
 * 响应结果封装类
 */
public class ResultUtils {
    /**
     * 成功
     *
     * @param data 数据
     * @param <T> 数据类型
     * @return 响应
     */
    public static <T> BaseResponse<T> success(T data){
        return new BaseResponse<>(0,"ok",data);
    }

    /**
     * 失败
     *
     * @param errorCode
     * @return 响应
     */
    public static BaseResponse<?> error(ErrorCode errorCode) {
        return new BaseResponse<>(errorCode);
    }

    /**
     *
     * @param code
     * @param message
     * @return 响应
     */
    public static BaseResponse<?> error(int code, String message) {
        return new BaseResponse<>(code,message,null);
    }
    public static BaseResponse<?> error(ErrorCode errorCode,String message) {
        return new BaseResponse<>(errorCode.getCode(),null,message);
    }
    /**
     * public String hello(@RequestParam(name = "name", defaultValue = "unknown user") String name) {
     *         return "Hello " + name;
     *   }改善
     * public BaseResponse<String> hello(@RequestParam(name = "name", defaultValue = "unknown user") String name) {
     *         return new BaseResponse<>(200,"Hello"+name);
     *   }
     *   public BaseResponse<String> hello(@RequestParam(name = "name", defaultValue = "unknown user") String name) {
     *         return ResultUtils.success("Hello"+name);
     *   }
     */

}
