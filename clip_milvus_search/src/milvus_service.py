"""
Milvus 向量数据库服务
基于 Zilliz 博客: CLIP+Milvus，多模态embedding如何用于以文搜图

功能：
- 创建集合 (3个字段: id, vectors, filepath)
- 插入图片向量数据
- 创建索引 (IVF_FLAT, COSINE)
- 加载集合到内存
- 向量相似度搜索
"""

import time
from pymilvus import MilvusClient, DataType
from config import (
    MILVUS_URI, COLLECTION_NAME, VECTOR_DIM,
    INDEX_TYPE, METRIC_TYPE, INDEX_NLIST
)


class MilvusService:
    """Milvus 向量数据库服务类"""

    def __init__(self, uri=None, collection_name=None):
        """
        初始化 Milvus 客户端

        Args:
            uri: Milvus 服务地址，默认使用 config 中的配置
            collection_name: Collection 名称，默认使用 config 中的配置
        """
        self.uri = uri or MILVUS_URI
        self.collection_name = collection_name or COLLECTION_NAME
        self.milvus_client = MilvusClient(uri=self.uri)
        print("-" * 50)
        print(f"Milvus Client Connected: {self.uri}")
        print(f"Collection Name: {self.collection_name}")
        print("-" * 50)

    def create_schema(self):
        """
        创建 Collection Schema

        Returns:
            schema: Collection 的模式对象

        Schema 包含 3 个字段：
        - id: INT64, 主键，自增
        - vectors: FLOAT_VECTOR, 512 维向量
        - filepath: VARCHAR, 图片路径，最大 200 字符
        """
        schema = self.milvus_client.create_schema(
            auto_id=True,           # 自动生成主键 ID
            enable_dynamic_field=True,
            description="Chinese-CLIP image embeddings collection"
        )

        # 添加字段
        schema.add_field(
            field_name="id",
            datatype=DataType.INT64,
            description='image id',
            is_primary=True
        )
        schema.add_field(
            field_name="vectors",
            datatype=DataType.FLOAT_VECTOR,
            description='embedding vectors',
            dim=VECTOR_DIM
        )
        schema.add_field(
            field_name="filepath",
            datatype=DataType.VARCHAR,
            description='file path',
            max_length=200
        )

        return schema

    def create_collection(self, collection_name=None, schema=None, shards_num=2):
        """
        创建 Collection

        Args:
            collection_name: 集合名称
            schema: Collection 的模式对象
            shards_num: 分片数量

        Returns:
            bool: 创建是否成功
        """
        collection_name = collection_name or self.collection_name

        if schema is None:
            schema = self.create_schema()

        try:
            self.milvus_client.create_collection(
                collection_name=collection_name,
                schema=schema,
                shards_num=shards_num
            )
            print(f"开始创建集合: {collection_name}")
        except Exception as e:
            print(f"创建集合的过程中出现了错误: {e}")
            return False

        # 等待集合创建成功
        return self._wait_for_collection(collection_name)

    def _wait_for_collection(self, collection_name, timeout=3):
        """
        等待集合创建成功

        Args:
            collection_name: 集合名称
            timeout: 超时时间 (秒)

        Returns:
            bool: 是否创建成功
        """
        start_time = time.time()
        while True:
            if self.milvus_client.has_collection(collection_name):
                print(f"集合 {collection_name} 创建成功")
                return True
            elif time.time() - start_time > timeout:
                print(f"创建集合 {collection_name} 超时")
                return False
            time.sleep(1)

    def check_and_drop_collection(self, collection_name=None):
        """
        检查并删除已存在的同名集合

        Args:
            collection_name: 集合名称

        Returns:
            bool: 删除是否成功或集合不存在
        """
        collection_name = collection_name or self.collection_name

        if self.milvus_client.has_collection(collection_name):
            print(f"集合 {collection_name} 已经存在，开始删除...")
            try:
                self.milvus_client.drop_collection(collection_name)
                print(f"删除集合: {collection_name}")
                return True
            except Exception as e:
                print(f"删除集合时出现错误: {e}")
                return False
        return True

    def create_index(self, collection_name=None):
        """
        创建向量索引

        使用 IVF_FLAT 倒排索引，余弦相似度度量

        Args:
            collection_name: 集合名称

        Returns:
            bool: 创建是否成功
        """
        collection_name = collection_name or self.collection_name

        index_params = self.milvus_client.prepare_index_params()
        index_params.add_index(
            index_name="IVF_FLAT",
            field_name="vectors",
            index_type=INDEX_TYPE,
            metric_type=METRIC_TYPE,
            params={"nlist": INDEX_NLIST}
        )

        try:
            self.milvus_client.create_index(
                collection_name=collection_name,
                index_params=index_params
            )
            print(f"索引创建成功: {INDEX_TYPE}, {METRIC_TYPE}")
            return True
        except Exception as e:
            print(f"创建索引时出现错误: {e}")
            return False

    def load_collection(self, collection_name=None):
        """
        加载集合到内存

        Args:
            collection_name: 集合名称

        Returns:
            bool: 加载是否成功
        """
        collection_name = collection_name or self.collection_name

        print(f"正在加载集合 {collection_name}")
        try:
            self.milvus_client.load_collection(collection_name=collection_name)
            print(f"集合 {collection_name} 加载完成")
            return True
        except Exception as e:
            print(f"加载集合时出现错误: {e}")
            return False

    def get_load_state(self, collection_name=None):
        """
        获取集合加载状态

        Args:
            collection_name: 集合名称

        Returns:
            str: 加载状态 ('Loaded' 或其他)
        """
        collection_name = collection_name or self.collection_name
        state = self.milvus_client.get_load_state(collection_name=collection_name)
        return str(state.get('state', 'Unknown'))

    def insert(self, collection_name=None, data=None):
        """
        插入向量数据

        Args:
            collection_name: 集合名称
            data: 要插入的数据列表，每个元素包含 vectors 和 filepath

        Returns:
            dict: 插入结果
        """
        collection_name = collection_name or self.collection_name

        try:
            res = self.milvus_client.insert(
                collection_name=collection_name,
                data=data
            )
            return res
        except Exception as e:
            print(f"插入数据时出现错误: {e}")
            raise

    def search(self, collection_name=None, vector=None, field_name="vectors",
              limit=10, output_fields=None):
        """
        向量相似度搜索

        Args:
            collection_name: 集合名称
            vector: 查询向量
            field_name: 搜索的向量字段名
            limit: 返回结果数量
            output_fields: 要返回的字段列表

        Returns:
            list: 搜索结果列表
        """
        collection_name = collection_name or self.collection_name
        if output_fields is None:
            output_fields = ["filepath"]

        try:
            res = self.milvus_client.search(
                collection_name=collection_name,
                data=[vector],  # 需要是列表形式
                anns_field=field_name,
                limit=limit,
                output_fields=output_fields
            )
            return res
        except Exception as e:
            print(f"搜索时出现错误: {e}")
            raise

    def query(self, collection_name=None, output_fields=None):
        """
        查询集合中的数据

        Args:
            collection_name: 集合名称
            output_fields: 要返回的字段列表，如 ["count(*)"]

        Returns:
            list: 查询结果
        """
        collection_name = collection_name or self.collection_name

        try:
            res = self.milvus_client.query(
                collection_name=collection_name,
                output_fields=output_fields or ["count(*)"]
            )
            return res
        except Exception as e:
            print(f"查询时出现错误: {e}")
            raise

    def delete_collection(self, collection_name=None):
        """
        删除集合

        Args:
            collection_name: 集合名称

        Returns:
            bool: 删除是否成功
        """
        collection_name = collection_name or self.collection_name

        try:
            self.milvus_client.drop_collection(collection_name)
            print(f"集合 {collection_name} 已删除")
            return True
        except Exception as e:
            print(f"删除集合时出现错误: {e}")
            return False


def setup_collection(milvus_service):
    """
    设置集合的完整流程：
    1. 删除已存在的同名集合
    2. 创建新集合
    3. 创建索引
    4. 加载集合到内存

    Args:
        milvus_service: MilvusService 实例
    """
    collection_name = milvus_service.collection_name

    # 1. 删除已存在的同名集合
    milvus_service.check_and_drop_collection(collection_name)

    # 2. 创建新集合
    schema = milvus_service.create_schema()
    milvus_service.create_collection(collection_name, schema)

    # 3. 创建索引
    milvus_service.create_index(collection_name)

    # 4. 加载集合到内存
    milvus_service.load_collection(collection_name)


# 全局单例
_milvus_service = None


def get_milvus_service():
    """获取全局 Milvus 服务实例"""
    global _milvus_service
    if _milvus_service is None:
        _milvus_service = MilvusService()
    return _milvus_service


if __name__ == "__main__":
    # 测试代码
    milvus_service = MilvusService()

    # 设置集合
    setup_collection(milvus_service)

    # 验证加载状态
    state = milvus_service.get_load_state()
    print(f"集合加载状态: {state}")

    # 查询数据数量
    count_result = milvus_service.query(output_fields=["count(*)"])
    print(f"集合中数据数量: {count_result}")
