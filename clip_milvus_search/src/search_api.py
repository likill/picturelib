"""
FastAPI 搜索服务
基于 Zilliz 博客: CLIP+Milvus，多模态embedding如何用于以文搜图

提供 RESTful API 接口：
- POST /search - 文本搜图
- POST /search/image - 以图搜图
- POST /index - 添加单张图片到索引
- GET /health - 健康检查
- GET /stats - 获取集合统计信息
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import uvicorn

from src.clip_service import CLIPService, get_clip_service
from src.milvus_service import MilvusService, get_milvus_service


# ==================== 数据模型 ====================

class SearchRequest(BaseModel):
    """搜索请求模型"""
    text: str
    top_k: int = 10


class ImageSearchRequest(BaseModel):
    """图片搜索请求模型"""
    image_url: str  # 图片 URL
    top_k: int = 10


class IndexRequest(BaseModel):
    """索引请求模型"""
    image_url: str  # 图片 URL
    picture_id: Optional[str] = None  # 可选的图片 ID


class SearchResult(BaseModel):
    """单个搜索结果"""
    rank: int  # 排名
    filepath: str  # 文件路径
    score: float  # 相似度得分


class SearchResponse(BaseModel):
    """搜索响应模型"""
    query: str
    results: List[SearchResult]
    total: int


class IndexResponse(BaseModel):
    """索引响应模型"""
    success: bool
    message: str


class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str
    clip_model: str
    milvus_connected: bool
    collection_name: str


# ==================== FastAPI 应用 ====================

app = FastAPI(
    title="CLIP + Milvus 多模态以文搜图服务",
    description="基于 Chinese-CLIP 和 Milvus 的以文搜图和以图搜图 API",
    version="1.0.0"
)

# 全局服务实例
_clip_service: Optional[CLIPService] = None
_milvus_service: Optional[MilvusService] = None


@app.on_event("startup")
async def startup_event():
    """应用启动时初始化服务"""
    global _clip_service, _milvus_service
    try:
        _clip_service = get_clip_service()
        _milvus_service = get_milvus_service()
        print("=" * 50)
        print("CLIP + Milvus 服务已启动")
        print("=" * 50)
    except Exception as e:
        print(f"服务初始化失败: {e}")
        raise


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    健康检查接口

    Returns:
        HealthResponse: 服务健康状态
    """
    try:
        # 检查 Milvus 连接
        milvus_connected = _milvus_service is not None

        return HealthResponse(
            status="healthy" if milvus_connected else "degraded",
            clip_model=_clip_service.model_name if _clip_service else "not loaded",
            milvus_connected=milvus_connected,
            collection_name=_milvus_service.collection_name if _milvus_service else "unknown"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/search", response_model=SearchResponse)
async def search_by_text(request: SearchRequest):
    """
    以文搜图接口

    Args:
        request: SearchRequest，包含查询文本和返回数量

    Returns:
        SearchResponse: 搜索结果列表
    """
    try:
        # 1. 将文本编码为向量
        query_embedding = _clip_service.encode_text([request.text])[0]

        # 2. 在 Milvus 中搜索
        search_results = _milvus_service.search(
            vector=query_embedding,
            field_name="vectors",
            limit=request.top_k,
            output_fields=["filepath"]
        )

        # 3. 格式化结果
        results = []
        for i, hit in enumerate(search_results[0]):
            results.append(SearchResult(
                rank=i + 1,
                filepath=hit["entity"]["filepath"],
                score=hit["distance"]
            ))

        return SearchResponse(
            query=request.text,
            results=results,
            total=len(results)
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/search/image", response_model=SearchResponse)
async def search_by_image(request: ImageSearchRequest):
    """
    以图搜图接口

    Args:
        request: ImageSearchRequest，包含图片 URL 和返回数量

    Returns:
        SearchResponse: 搜索结果列表
    """
    try:
        # 1. 从 URL 下载图片并编码
        query_embedding = _clip_service.encode_image_from_url(request.image_url)

        # 2. 在 Milvus 中搜索
        search_results = _milvus_service.search(
            vector=query_embedding,
            field_name="vectors",
            limit=request.top_k,
            output_fields=["filepath"]
        )

        # 3. 格式化结果
        results = []
        for i, hit in enumerate(search_results[0]):
            results.append(SearchResult(
                rank=i + 1,
                filepath=hit["entity"]["filepath"],
                score=hit["distance"]
            ))

        return SearchResponse(
            query=request.image_url,
            results=results,
            total=len(results)
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/index", response_model=IndexResponse)
async def index_image(request: IndexRequest):
    """
    添加单张图片到索引

    Args:
        request: IndexRequest，包含图片 URL

    Returns:
        IndexResponse: 索引结果
    """
    try:
        # 1. 从 URL 下载图片并编码
        embedding = _clip_service.encode_image_from_url(request.image_url)

        # 2. 插入 Milvus
        data = [{
            "vectors": embedding,
            "filepath": request.image_url
        }]

        _milvus_service.insert(data=data)

        return IndexResponse(
            success=True,
            message=f"图片 {request.image_url} 已成功索引"
        )

    except Exception as e:
        return IndexResponse(
            success=False,
            message=f"索引失败: {str(e)}"
        )


@app.get("/stats")
async def get_stats():
    """
    获取集合统计信息

    Returns:
        dict: 统计信息
    """
    try:
        count_result = _milvus_service.query(output_fields=["count(*)"])
        count = count_result[0].get("count(*)", 0) if count_result else 0

        return {
            "collection_name": _milvus_service.collection_name,
            "total_images": count,
            "vector_dim": 512,
            "index_type": "IVF_FLAT",
            "metric_type": "COSINE"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 启动函数 ====================

def run_server(host="0.0.0.0", port=8000):
    """
    启动 FastAPI 服务

    Args:
        host: 监听地址
        port: 监听端口
    """
    uvicorn.run(
        "src.search_api:app",
        host=host,
        port=port,
        reload=True
    )


if __name__ == "__main__":
    run_server()
