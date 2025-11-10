package com.jiaxin.zhupicture.common;

import lombok.Data;

import java.io.Serializable;

/**
 * 通用的删除请求类
 */
@Data
public class DeleteRequest implements Serializable {
    private long id;
    private static final long serversionUID = 1L;
}
