-- ============================================================
-- 智慧路灯节能系统 (Smart Streetlight Energy-Saving System)
-- 数据库初始化脚本
-- 数据库: smart_streetlight
-- 字符集: utf8mb4
-- ============================================================

CREATE DATABASE IF NOT EXISTS `smart_streetlight`
    DEFAULT CHARACTER SET utf8mb4
    DEFAULT COLLATE utf8mb4_unicode_ci;

USE `smart_streetlight`;

-- ============================================================
-- 1. 设备表 (devices)
--    主表，其他表通过 device_id 外键关联
-- ============================================================
DROP TABLE IF EXISTS `alarm_logs`;
DROP TABLE IF EXISTS `control_logs`;
DROP TABLE IF EXISTS `light_data`;
DROP TABLE IF EXISTS `threshold_configs`;
DROP TABLE IF EXISTS `conversations`;
DROP TABLE IF EXISTS `messages`;
DROP TABLE IF EXISTS `db_sync_meta`;
DROP TABLE IF EXISTS `devices`;
DROP TABLE IF EXISTS `users`;

CREATE TABLE `devices` (
    `id`                INT           NOT NULL AUTO_INCREMENT,
    `device_code`       VARCHAR(64)   NOT NULL COMMENT '设备编号（唯一）',
    `device_name`       VARCHAR(100)  NOT NULL COMMENT '设备名称',
    `location`          VARCHAR(255)  DEFAULT NULL COMMENT '安装位置',
    `latitude`          FLOAT         DEFAULT NULL COMMENT 'GPS 纬度',
    `longitude`         FLOAT         DEFAULT NULL COMMENT 'GPS 经度',
    `status`            VARCHAR(20)   NOT NULL DEFAULT 'offline' COMMENT 'online / offline',
    `last_heartbeat_at` DATETIME      DEFAULT NULL COMMENT '最后心跳时间',
    `created_at`        DATETIME      NOT NULL COMMENT '创建时间',
    `updated_at`        DATETIME      NOT NULL COMMENT '更新时间',
    `deleted_at`        DATETIME      DEFAULT NULL COMMENT '软删除时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_device_code` (`device_code`),
    KEY `ix_devices_id` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- 2. 用户表 (users)
--    登录认证、角色权限
-- ============================================================
CREATE TABLE `users` (
    `id`            INT           NOT NULL AUTO_INCREMENT,
    `username`      VARCHAR(64)   NOT NULL COMMENT '用户名（唯一）',
    `password_hash` VARCHAR(255)  NOT NULL COMMENT 'bcrypt 密码哈希',
    `role`          VARCHAR(20)   NOT NULL DEFAULT 'user' COMMENT 'admin / maintainer / user',
    `is_active`     TINYINT(1)    NOT NULL DEFAULT 1 COMMENT '是否启用',
    `created_at`    DATETIME      NOT NULL COMMENT '创建时间',
    `updated_at`    DATETIME      NOT NULL COMMENT '更新时间',
    `deleted_at`    DATETIME      DEFAULT NULL COMMENT '软删除时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_username` (`username`),
    KEY `ix_users_id` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- 3. 阈值配置表 (threshold_configs)
--    每个设备一条，自动控制开关灯的光照阈值
-- ============================================================
CREATE TABLE `threshold_configs` (
    `id`             INT        NOT NULL AUTO_INCREMENT,
    `device_id`      INT        NOT NULL COMMENT '关联设备 ID',
    `low_threshold`  INT        NOT NULL DEFAULT 100 COMMENT '开灯阈值（光照低于此值开灯）',
    `high_threshold` INT        NOT NULL DEFAULT 300 COMMENT '关灯阈值（光照高于此值关灯）',
    `enabled`        TINYINT(1) NOT NULL DEFAULT 1 COMMENT '是否启用自动控制',
    `updated_at`     DATETIME   NOT NULL COMMENT '更新时间',
    `deleted_at`     DATETIME   DEFAULT NULL COMMENT '软删除时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_device_id` (`device_id`),
    KEY `ix_threshold_configs_id` (`id`),
    CONSTRAINT `fk_threshold_configs_device` FOREIGN KEY (`device_id`)
        REFERENCES `devices` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- 4. 光照数据表 (light_data)
--    设备上报的传感器数据，追加写入
-- ============================================================
CREATE TABLE `light_data` (
    `id`              INT         NOT NULL AUTO_INCREMENT,
    `device_id`       INT         NOT NULL COMMENT '关联设备 ID',
    `light_intensity` INT         NOT NULL COMMENT '光照强度（lux）',
    `lamp_status`     VARCHAR(20) NOT NULL COMMENT '灯具状态 on / off',
    `voltage`         FLOAT       DEFAULT NULL COMMENT '电压（V）',
    `reported_at`     DATETIME    NOT NULL COMMENT '数据上报时间',
    `created_at`      DATETIME    NOT NULL COMMENT '记录创建时间',
    `deleted_at`      DATETIME    DEFAULT NULL COMMENT '软删除时间',
    PRIMARY KEY (`id`),
    KEY `ix_light_data_id` (`id`),
    KEY `ix_light_data_device_id` (`device_id`),
    KEY `ix_light_data_reported_at` (`reported_at`),
    CONSTRAINT `fk_light_data_device` FOREIGN KEY (`device_id`)
        REFERENCES `devices` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- 5. 控制日志表 (control_logs)
--    记录对设备的每一次控制操作
-- ============================================================
CREATE TABLE `control_logs` (
    `id`              INT           NOT NULL AUTO_INCREMENT,
    `device_id`       INT           NOT NULL COMMENT '关联设备 ID',
    `command`         VARCHAR(50)   NOT NULL COMMENT '控制指令 TURN_ON / TURN_OFF / SET_BRIGHTNESS',
    `source`          VARCHAR(20)   NOT NULL DEFAULT 'manual' COMMENT 'manual / auto / agent',
    `result`          VARCHAR(20)   NOT NULL DEFAULT 'pending' COMMENT 'pending / success / fail',
    `request_payload` JSON          DEFAULT NULL COMMENT '请求参数',
    `reply_payload`   JSON          DEFAULT NULL COMMENT '回复内容',
    `created_at`      DATETIME      NOT NULL COMMENT '创建时间',
    `deleted_at`      DATETIME      DEFAULT NULL COMMENT '软删除时间',
    PRIMARY KEY (`id`),
    KEY `ix_control_logs_id` (`id`),
    KEY `ix_control_logs_device_id` (`device_id`),
    CONSTRAINT `fk_control_logs_device` FOREIGN KEY (`device_id`)
        REFERENCES `devices` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- 6. 告警日志表 (alarm_logs)
--    设备离线、异常等告警记录
-- ============================================================
CREATE TABLE `alarm_logs` (
    `id`            INT           NOT NULL AUTO_INCREMENT,
    `device_id`     INT           NOT NULL COMMENT '关联设备 ID',
    `alarm_type`    VARCHAR(50)   NOT NULL COMMENT '告警类型 offline / voltage / lamp_fault',
    `alarm_level`   VARCHAR(20)   NOT NULL DEFAULT 'warning' COMMENT 'warning / critical',
    `alarm_content` VARCHAR(500)  NOT NULL COMMENT '告警内容',
    `handled`       TINYINT(1)    NOT NULL DEFAULT 0 COMMENT '是否已处理',
    `handled_at`    DATETIME      DEFAULT NULL COMMENT '处理时间',
    `created_at`    DATETIME      NOT NULL COMMENT '创建时间',
    `deleted_at`    DATETIME      DEFAULT NULL COMMENT '软删除时间',
    PRIMARY KEY (`id`),
    KEY `ix_alarm_logs_id` (`id`),
    KEY `ix_alarm_logs_device_id` (`device_id`),
    CONSTRAINT `fk_alarm_logs_device` FOREIGN KEY (`device_id`)
        REFERENCES `devices` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- 7. 同步元信息表 (db_sync_meta)
--    记录云端到本地同步进度
-- ============================================================
CREATE TABLE `db_sync_meta` (
    `id`              INT         NOT NULL AUTO_INCREMENT,
    `table_name`      VARCHAR(64) NOT NULL COMMENT '表名',
    `last_synced_id`  INT         NOT NULL DEFAULT 0 COMMENT '最后同步的 ID（追加表）',
    `last_synced_at`  DATETIME    DEFAULT NULL COMMENT '最后同步时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_table_name` (`table_name`),
    KEY `ix_db_sync_meta_id` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
