package com.jiaxin.zhupicture.model.dto.user;

import lombok.Getter;

import java.io.Serializable;

@Getter
public class UserRegisterRequest implements Serializable {


    private static final long serialVersionUID = -7143511303396969164L;

    private String userAccount;


    private String userPassword;


    private String  checkPassword;
}
