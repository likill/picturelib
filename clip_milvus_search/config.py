"""
CLIP + Milvus 多模态以文搜图配置文件
基于 Zilliz 博客: CLIP+Milvus，多模态embedding如何用于以文搜图
"""

import os

# ==================== Milvus 配置 ====================
# Milvus 服务地址 (使用 Milvus Lite 本地模式)
MILVUS_URI = "http://localhost:19530"

# Collection 名称
COLLECTION_NAME = "multimodal_chinese_clip"

# 向量维度 (ViT-B-16 模型生成 512 维向量)
VECTOR_DIM = 512

# 索引配置
INDEX_TYPE = "IVF_FLAT"  # 倒排索引，检索效率高，准确性也不错
METRIC_TYPE = "COSINE"   # 余弦相似度
INDEX_NLIST = 512        # 聚类中心数量

# ==================== Chinese-CLIP 模型配置 ====================
# 可用模型: 'ViT-B-16', 'ViT-L-14', 'ViT-L-14-336', 'ViT-H-14', 'RN50'
MODEL_NAME = "ViT-B-16"

# 模型下载保存路径
MODEL_DOWNLOAD_ROOT = "./chinese_clip_model"

# ==================== 数据处理配置 ====================
# 图片批次大小
BATCH_SIZE = 300

# 支持的图片格式
IMAGE_EXTENSIONS = ['*.JPEG', '*.jpg', '*.png']

# ==================== zhupicture 数据库配置 ====================
# 用于从原项目数据库读取图片进行索引
DB_CONFIG = {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "your_password",
    "database": "zhupicture"
}

# ==================== API 服务配置 ====================
API_HOST = "0.0.0.0"
API_PORT = 8000

# ==================== 其他配置 ====================
# 日志级别
LOG_LEVEL = "INFO"
