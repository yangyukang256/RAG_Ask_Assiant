"""阿里云百炼 API 封装"""
from typing import AsyncGenerator, Optional
from langchain_openai import ChatOpenAI
from langchain_community.embeddings import DashScopeEmbeddings
from app.config import settings

# 阿里云百炼兼容 OpenAI 格式
DASHSCOPE_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"


class LLMService:
    """阿里云百炼 LLM & Embedding 服务"""

    def __init__(self):
        self._llm_cache = {}
        self._embeddings_instance = None

    def get_llm(self, model_name: Optional[str] = None, streaming: bool = True) -> ChatOpenAI:
        """获取通义千问 LLM 实例"""
        model = model_name or settings.LLM_MODEL_NAME
        cache_key = f"{model}_{streaming}"

        if cache_key in self._llm_cache:
            return self._llm_cache[cache_key]

        llm = ChatOpenAI(
            model=model,
            openai_api_key=settings.DASHSCOPE_API_KEY,
            openai_api_base=DASHSCOPE_BASE_URL,
            temperature=settings.LLM_TEMPERATURE,
            streaming=streaming,
            max_tokens=4096,
        )
        self._llm_cache[cache_key] = llm
        return llm

    def get_embeddings(self) -> DashScopeEmbeddings:
        """获取百炼 Embedding 实例"""
        if self._embeddings_instance:
            return self._embeddings_instance

        self._embeddings_instance = DashScopeEmbeddings(
            model=settings.EMBEDDING_MODEL_NAME,
            dashscope_api_key=settings.DASHSCOPE_API_KEY,
        )
        return self._embeddings_instance

    async def stream_generate(self, messages: list, model: Optional[str] = None) -> AsyncGenerator[str, None]:
        """流式生成"""
        llm = self.get_llm(model_name=model, streaming=True)
        # LangChain 的流式调用
        async for chunk in llm.astream(messages):
            if hasattr(chunk, "content") and chunk.content:
                yield chunk.content

    async def generate(self, messages: list, model: Optional[str] = None) -> str:
        """非流式生成"""
        llm = self.get_llm(model_name=model, streaming=False)
        response = await llm.ainvoke(messages)
        return response.content

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """批量生成文本向量"""
        embeddings = self.get_embeddings()
        return embeddings.embed_documents(texts)

    def embed_query(self, text: str) -> list[float]:
        """生成查询向量"""
        embeddings = self.get_embeddings()
        return embeddings.embed_query(text)


# 全局单例
llm_service = LLMService()