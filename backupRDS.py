#!/usr/bin/env python
# -*- coding: utf-8 -*-
# time: 2023/3/31 10:40
# file: rds_backup.py
# author: qinxi
# email: 1023495336@qq.com

import os
import datetime
import logging
import time

import pymysql
import tarfile
import traceback

# 阿里云RDS数据库连接配置
rds_config = {
    'host': 'rm-*********.mysql.zhangbei.rds.aliyuncs.com',
    'user': '*****',
    'password': 'd4********#PR',
    'port': 3306,
}

def mkdir(dir):
    if not os.path.exists(dir):
       os.makedirs(dir)

# 获取当前时间
now = datetime.datetime.now().strftime('%Y%m%d%H%M')
now_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

def rm_file(dir_path):
    # 获取当前时间
    current_time = time.time()

    # 遍历目录中的文件
    for file in os.listdir(dir_path):
        file_path = os.path.join(dir_path, file)
        # 获取文件的修改时间
        mod_time = os.path.getmtime(file_path)
        # 计算文件的年龄
        file_age = current_time - mod_time
        # 如果文件的年龄超过两天（单位为秒）
        if file_age > 2 * 24 * 60 * 60:
            # 删除文件
            os.remove(file_path)
            time.sleep(0.1)
            print('正在删除：',file_path)

current_date = datetime.datetime.now().strftime('%Y-%m-%d-%H')
# yesterday_date = '{}'.format((datetime.datetime.now() - datetime.timedelta(days=1)).strftime('%Y-%m-%d-%H'))

# 备份文件保存路径
backup_path = '/data/RDSbackup/' + current_date + '/'
backup_tarfile = 'RDSbackup.tar.gz'
mkdir(backup_path)

# 日志记录配置
log_path = backup_path +'/logs'
log_file = 'backup.log'
mkdir(log_path)


# 初始化日志记录器
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler(os.path.join(log_path, log_file)),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger()

try:
    # 连接数据库
    conn = pymysql.connect(**rds_config)
    cursor = conn.cursor()

    # 查询数据库列表
    sql = "SELECT schema_name FROM information_schema.SCHEMATA WHERE schema_name NOT IN ('information_schema', 'mysql', 'performance_schema', 'sys')"
    cursor.execute(sql)
    databases = [row[0] for row in cursor.fetchall()]
    # 关闭数据库连接
    cursor.close()
    conn.close()

    # 遍历每个数据库
    for database_name in databases:
        mkdir(backup_path + database_name)

        # 连接数据库
        conn = pymysql.connect(**rds_config, database=database_name)
        cursor = conn.cursor()

        # 查询表列表
        sql = "SELECT table_name FROM information_schema.TABLES WHERE table_schema = %s"
        cursor.execute(sql, database_name)
        tables = [row[0] for row in cursor.fetchall()]

        # 遍历每个表
        for table_name in tables:
            # 构造备份文件名和备份SQL语句
            backup_file = f"{table_name}_{now}_sql"
            backup_full_path = os.path.join(backup_path, database_name, backup_file)
            backup_sql = f"mysqldump --no-create-db --single-transaction --default-character-set=utf8mb4 --set-gtid-purged=OFF -u{rds_config['user']} -h{rds_config['host']} -p{rds_config['password']} {database_name} {table_name} | gzip > {backup_full_path}.tar.gz"

            try:
                # 执行备份SQL语句
                os.system(backup_sql)

                # 记录备份日志
                logger.info(f"Backup {database_name}.{table_name} to {backup_full_path} success.")
                print(f"{now_time} Backup {database_name}.{table_name} to {backup_full_path} success.")

            except Exception as e:
                # 记录备份失败日志
                logger.error(f"Backup {database_name}.{table_name} to {backup_full_path} failed.")
                print(f"{now_time} Backup {database_name}.{table_name} to {backup_full_path} failed.")
                logger.error(f"Error occurred: {e}")
                logger.error(traceback.format_exc())

        #关闭数据库连接
        cursor.close()
        conn.close()

    # 压缩备份文件
    with tarfile.open(os.path.join(backup_path, backup_tarfile), "w:gz") as tar:
        tar.add(backup_path)

    # 记录备份完成日志
    logger.info(f"Backup finished. The compressed backup file is saved in {os.path.join(backup_path, backup_tarfile)}")
    print(f"{now_time} Backup finished. The compressed backup file is saved in {os.path.join(backup_path, backup_tarfile)}")
    # 清除两天前的备份，释放磁盘空间
    if backup_path:
       rm_file(backup_path)

except Exception as e:
    # 记录异常日志
    logger.error(f"Error occurred: {e}")
    logger.error(traceback.format_exc())
    
    
    
    
    
