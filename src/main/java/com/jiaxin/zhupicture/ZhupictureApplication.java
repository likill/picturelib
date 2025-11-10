package com.jiaxin.zhupicture;

import org.mybatis.spring.annotation.MapperScan;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.EnableAspectJAutoProxy;
import org.springframework.scheduling.annotation.EnableAsync;

@SpringBootApplication
@MapperScan("com.jiaxin.zhupicture.mapper")
@EnableAsync
@EnableAspectJAutoProxy(exposeProxy = true)//代理，功能的增强
public class ZhupictureApplication {

    public static void main(String[] args) {
        SpringApplication.run(ZhupictureApplication.class, args);
    }

}
