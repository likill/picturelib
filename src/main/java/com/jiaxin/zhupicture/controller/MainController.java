package com.jiaxin.zhupicture.controller;

import com.jiaxin.zhupicture.common.BaseResponse;
import com.jiaxin.zhupicture.common.ResultUtils;
import com.jiaxin.zhupicture.exception.ErrorCode;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.io.File;
import java.io.IOException;

@RestController//表示他是一个接口
@RequestMapping("/")//接口路径，用/表示根路径
@Slf4j
public class MainController {

    @GetMapping("/health")
    public BaseResponse<?> health() {
        return ResultUtils.error(500,"Notok");
    }

}
