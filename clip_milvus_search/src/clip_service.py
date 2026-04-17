"""
CLIP 向量化服务
基于 Zilliz 博客: CLIP+Milvus，多模态embedding如何用于以文搜图

使用 Chinese-CLIP 嵌入模型将图片和文本编码到同一个向量空间
- encode_image(): 图片 -> 向量 (512维)
- encode_text(): 文本 -> 向量 (512维)
"""

import torch
from PIL import Image
import cn_clip.clip as clip
from config import MODEL_NAME, MODEL_DOWNLOAD_ROOT, device


class CLIPService:
    """CLIP 向量化服务类"""

    def __init__(self, model_name=None, download_root=None, use_gpu=True):
        """
        初始化 CLIP 服务，加载模型和预处理函数

        Args:
            model_name: 模型名称，默认使用 config 中的配置
            download_root: 模型下载路径，默认使用 config 中的配置
            use_gpu: 是否使用 GPU，默认 True
        """
        self.model_name = model_name or MODEL_NAME
        self.download_root = download_root or MODEL_DOWNLOAD_ROOT
        self.device = "cuda" if use_gpu and torch.cuda.is_available() else "cpu"

        # 加载模型和预处理函数
        self.model, self.preprocess = clip.load_from_name(
            self.model_name,
            device=self.device,
            download_root=self.download_root
        )
        # 设置为评估模式，关闭 dropout 等训练特性
        self.model.eval()

        print("-" * 50)
        print(f"CLIP Model Loaded: {self.model_name}")
        print(f"Device: {self.device}")
        print("-" * 50)

    def encode_image(self, image_path):
        """
        将图片编码为向量

        Args:
            image_path: 图片路径 (本地路径或 URL)

        Returns:
            list: 512 维向量 (归一化后)
        """
        with torch.no_grad():
            # 打开图片文件
            raw_image = Image.open(image_path).convert('RGB')
            # 图片预处理 (归一化、缩放等)
            processed_image = self.preprocess(raw_image).unsqueeze(0).to(self.device)
            # 生成图片向量
            image_features = self.model.encode_image(processed_image)
            # 特征归一化
            image_features /= image_features.norm(dim=-1, keepdim=True)
            # 以列表形式返回向量
            return image_features.squeeze().tolist()

    def encode_text(self, text_list):
        """
        将文本列表编码为向量

        Args:
            text_list: 文本列表，如 ["枯藤老树昏鸦", "小桥流水人家"]

        Returns:
            list: 向量列表，每个文本对应一个 512 维归一化向量
        """
        with torch.no_grad():
            # 文本分词和特殊符号处理
            text_tokens = clip.tokenize(text_list).to(self.device)
            # 生成文本向量
            text_features = self.model.encode_text(text_tokens)
            # 特征归一化
            text_features /= text_features.norm(dim=-1, keepdim=True)
            # 以列表形式返回向量
            return [f.squeeze().tolist() for f in text_features]

    def encode_image_from_url(self, url):
        """
        从 URL 下载图片并编码

        Args:
            url: 图片 URL

        Returns:
            list: 512 维向量
        """
        import requests
        from io import BytesIO

        response = requests.get(url)
        image = Image.open(BytesIO(response.content)).convert('RGB')

        with torch.no_grad():
            processed_image = self.preprocess(image).unsqueeze(0).to(self.device)
            image_features = self.model.encode_image(processed_image)
            image_features /= image_features.norm(dim=-1, keepdim=True)
            return image_features.squeeze().tolist()


# 全局单例 (延迟加载)
_clip_service = None


def get_clip_service():
    """获取全局 CLIP 服务实例"""
    global _clip_service
    if _clip_service is None:
        _clip_service = CLIPService()
    return _clip_service


if __name__ == "__main__":
    # 测试代码
    clip_service = CLIPService()

    # 测试文本编码
    text_list = ["枯藤老树昏鸦", "小桥流水人家"]
    text_vectors = clip_service.encode_text(text_list)
    print(f"文本向量数量: {len(text_vectors)}")
    print(f"单个向量维度: {len(text_vectors[0])}")

    print("\n" + "-" * 50)

    # 测试图片编码 (如果存在测试图片)
    import os
    test_image_path = "query_image.jpg"
    if os.path.exists(test_image_path):
        image_vector = clip_service.encode_image(test_image_path)
        print(f"图片向量维度: {len(image_vector)}")
