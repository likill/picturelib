package com.jiaxin.zhupicture.model.enums;

import lombok.Getter;
import cn.hutool.core.util.ObjUtil;

@Getter
public enum UserRoleEnum {

    USER("用户", "user"),
    ADMIN("管理员", "admin");

    private final String text;
    private final String value;

    /**
     *
     * @param text
     * @param value
     */
    UserRoleEnum(String text, String value) {
        this.text = text;
        this.value = value;
    }

    public static UserRoleEnum getEnumByValue(String value) {
        if(ObjUtil.isEmpty(value)){
            return null;
        }
        for(UserRoleEnum userRoleEnum : UserRoleEnum.values()){
            if(userRoleEnum.value.equals(value)){
                return userRoleEnum;
            }
        }
//        Map<String, UserRoleEnum> map = new HashMap<>();
//        map.put("用户", USER);
//        map.put("管理员", ADMIN);
        return null;
    }
}
