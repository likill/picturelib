# CLIP + Milvus 多模态以文搜图

基于 [Zilliz 博客: CLIP+Milvus，多模态embedding如何用于以文搜图](https://zilliz.com.cn/blog/CLIP-Milvus-Multimodal-Embedding-Image-Search) 实现的完整项目。

## 原理概述

### CLIP (Contrastive Language-Image Pre-training)

CLIP 是一种多模态嵌入模型，能够将图像和文本编码到同一个向量空间，使得语义相近的概念在向量空间中距离更近。

**训练步骤**：
1. 准备图文配对的多模态数据集
2. 使用文本编码器和图片编码器分别编码文本和图片
3. 将文本和图片向量映射到同一个多模态向量空间
4. 通过对比学习，拉近正样本（相近概念）的距离，推远负样本的距离

### 以文搜图流程

```
用户输入文本 → CLIP 编码 → 文本向量 → Milvus 相似度搜索 → 返回匹配图片
```

## 项目结构

```
clip_milvus_search/
├── requirements.txt          # Python 依赖
├── config.py                # 配置文件
├── README.md                # 本文档
├── src/
│   ├── __init__.py
│   ├── clip_service.py      # CLIP 向量化服务
│   ├── milvus_service.py    # Milvus 集合管理
│   ├── search_api.py       # FastAPI 搜索接口
│   ├── index_images.py      # 图片索引脚本
│   └── main.py              # 启动入口
└── chinese_clip_model/       # Chinese-CLIP 模型目录（运行时自动下载）
```

## 快速开始

### 1. 安装依赖

```bash
cd clip_milvus_search
pip install -r requirements.txt
```

主要依赖：
- `pymilvus>=2.5.0` - 向量数据库客户端
- `cn_clip` - Chinese-CLIP 中文多模态嵌入模型
- `torch>=2.0.0` - 深度学习框架
- `fastapi>=0.100.0` - Web 框架
- `uvicorn>=0.23.0` - ASGI 服务器

### 2. 启动 Milvus Lite

Milvus Lite 是轻量级嵌入式向量数据库，适合开发测试。

```bash
pip install pymilvus
```

Milvus Lite 会自动在本地创建向量数据库文件，无需额外启动服务。

### 3. 下载 Chinese-CLIP 模型（可选）

首次运行时会自动下载模型到 `chinese_clip_model` 目录。

可用模型：
- `ViT-B-16` - 基础模型（默认）
- `ViT-L-14` - 大规模模型
- `ViT-L-14-336` - 高分辨率模型
- `ViT-H-14` - 超大规模模型
- `RN50` - ResNet 架构模型

### 4. 初始化集合

```bash
python src/main.py --setup
```

这会创建集合并设置索引。

## 使用方法

### 方式一：启动 API 服务

```bash
python src/main.py
# 或指定端口
python src/main.py --port 8080
```

服务启动后访问：
- API 地址: http://localhost:8000
- API 文档: http://localhost:8000/docs

### 方式二：Python 脚本使用

```python
from src.clip_service import CLIPService
from src.milvus_service import MilvusService, setup_collection

# 初始化服务
clip_service = CLIPService()
milvus_service = MilvusService()

# 设置集合
setup_collection(milvus_service)

# 以文搜图
query_text = ["枯藤老树昏鸦"]
query_embedding = clip_service.encode_text(query_text)[0]

results = milvus_service.search(
    vector=query_embedding,
    field_name="vectors",
    limit=10,
    output_fields=["filepath"]
)

print(results)
```

## API 接口

### POST /search - 以文搜图

```bash
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{"text": "枯藤老树昏鸦", "top_k": 5}'
```

响应：
```json
{
  "query": "枯藤老树昏鸦",
  "results": [
    {"rank": 1, "filepath": "xxx.jpg", "score": 0.95},
    {"rank": 2, "filepath": "yyy.jpg", "score": 0.89}
  ],
  "total": 2
}
```

### POST /search/image - 以图搜图

```bash
curl -X POST http://localhost:8000/search/image \
  -H "Content-Type: application/json" \
  -d '{"image_url": "https://example.com/image.jpg", "top_k": 5}'
```

### POST /index - 添加图片到索引

```bash
curl -X POST http://localhost:8000/index \
  -H "Content-Type: application/json" \
  -d '{"image_url": "https://example.com/image.jpg"}'
```

### GET /health - 健康检查

```bash
curl http://localhost:8000/health
```

### GET /stats - 集合统计

```bash
curl http://localhost:8000/stats
```

## 图片索引

### 从本地目录索引

```bash
python src/index_images.py --mode local --path ./images
```

### 从 zhupicture 数据库索引

需要先配置 `config.py` 中的数据库连接信息：

```python
DB_CONFIG = {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "your_password",
    "database": "zhupicture"
}
```

然后运行：

```bash
# 索引全部图片
python src/index_images.py --mode db

# 限制数量
python src/index_images.py --mode db --limit 100
```

### 索引单张图片

```bash
python src/index_images.py --mode single --url https://example.com/image.jpg
```

## 配置说明

主要配置项在 `config.py` 中：

```python
# Milvus 配置
MILVUS_URI = "http://localhost:19530"  # Milvus 服务地址
COLLECTION_NAME = "multimodal_chinese_clip"  # Collection 名称
VECTOR_DIM = 512  # 向量维度 (ViT-B-16 模型)

# Chinese-CLIP 模型配置
MODEL_NAME = "ViT-B-16"  # 可选: ViT-B-16, ViT-L-14, etc.
MODEL_DOWNLOAD_ROOT = "./chinese_clip_model"  # 模型保存路径

# 索引配置
INDEX_TYPE = "IVF_FLAT"  # 索引类型
METRIC_TYPE = "COSINE"  # 度量方式 (余弦相似度)
```

## 数据集准备

博客中使用的是 LHQ1024_jpg 数据集（ landscapes 图片）：

1. 下载数据集（提取码: 7d88）
2. 解压后目录结构：
   - `query_image.jpg` - 查询用图片
   - `lhq_1024_jpg_5000/` - 5000 张风景图片
   - `chinese_clip_model/` - 预下载的模型文件

## 核心代码解析

### CLIP 向量化

```python
def encode_image(image_path):
    with torch.no_grad():
        raw_image = Image.open(image_path).convert('RGB')
        processed_image = preprocess(raw_image).unsqueeze(0).to(device)
        image_features = model.encode_image(processed_image)
        image_features /= image_features.norm(dim=-1, keepdim=True)
        return image_features.squeeze().tolist()

def encode_text(text_list):
    with torch.no_grad():
        text_tokens = clip.tokenize(text_list).to(device)
        text_features = model.encode_text(text_tokens)
        text_features /= text_features.norm(dim=-1, keepdim=True)
        return [f.squeeze().tolist() for f in text_features]
```

### Milvus 搜索

```python
def search(self, vector, field_name="vectors", limit=10):
    res = milvus_client.search(
        collection_name=collection_name,
        data=[vector],
        anns_field=field_name,
        limit=limit,
        output_fields=["filepath"]
    )
    return res
```

## 常见问题

### Q: 检索结果不理想？
A: 可能原因：
- 数据集中没有与查询概念相近的图片
- CLIP 模型的文本和图片编码器特征空间没有充分对齐
- 需要更多数据做微调

### Q: 如何处理图片下载失败？
A: 代码中有异常处理，单张图片失败不会影响整体流程。失败的图片会跳过并继续处理下一张。

### Q: 如何提高检索速度？
A: 可以调整 `INDEX_NLIST` 参数（聚类中心数量），值越大索引越精确但查询越慢。

## 参考资料

- [CLIP+Milvus，多模态embedding如何用于以文搜图](https://zilliz.com.cn/blog/CLIP-Milvus-Multimodal-Embedding-Image-Search)
- [Chinese-CLIP](https://github.com/OFA-Sys/Chinese-CLIP)
- [Milvus 向量数据库](https://milvus.io/)
- [pymilvus](https://github.com/milvus-io/pymilvus)
