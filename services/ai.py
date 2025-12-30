import json
from typing import List

from langchain_core.documents import Document
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

from core.ai import llm, vector_store


class AiService:
    async def chat(self, user_id: int, question: str, session_id: str):
        """
        AI 聊天接口 (融合三种 RAG 策略)
        """
        chat_message_list_key = f'chat:message:list:{user_id}:{session_id}'
        from core.redis_client import redis_client_manager as redis
        redis_client = redis.get_client()

        # ==================================================
        # 1. 获取并构建历史记录
        # ==================================================
        history_json_list = await redis_client.lrange(chat_message_list_key, -10, -1) or []
        history_messages = []
        for item in history_json_list:
            msg = json.loads(item)
            if msg['role'] == 'user':
                history_messages.append(HumanMessage(content=msg['content']))
            elif msg['role'] == 'assistant':
                history_messages.append(AIMessage(content=msg['content']))

        # ==================================================
        # 2. 【策略一：历史上下文重写】 (History Awareness)
        # 目的：处理指代消解 (如 "它怎么治" -> "甲流怎么治")
        # ==================================================
        standalone_question = await self.rewrite_query_based_on_history(question, history_messages)
        print(f"🧐 [策略1] 独立问题: {standalone_question}")

        # ==================================================
        # 3. 【策略二 & 三：多路扩展与分解】 (Expansion & Decomposition)
        # 目的：生成多个搜索视角和子问题
        # ==================================================
        # 这一步会生成一个列表，例如 ["甲流治疗方案", "儿童甲流用药", "甲流发烧护理"]
        queries_to_search = await self.generate_multi_queries(standalone_question)
        print(f"🚀 [策略2&3] 生成的搜索词: {queries_to_search}")

        # ==================================================
        # 4. 【并行向量检索 & 去重】 (Retrieval & Deduplication)
        # 目的：拿着所有搜索词去库里找，并合并结果
        # ==================================================
        all_docs = []

        # 遍历所有生成的查询词进行检索
        # 注意：vector_store.similarity_search 是同步的，这里用循环
        for q in queries_to_search:
            # 这里的 k=2 可以小一点，因为我们搜了很多次，总量会很多
            docs = vector_store.similarity_search(q, k=2)
            all_docs.extend(docs)

        # 【文档去重】：根据 page_content 去重，防止上下文重复
        unique_docs = self._deduplicate_documents(all_docs)
        print(f"📚 [最终] 检索到 {len(unique_docs)} 个不重复片段")

        # 构建上下文
        context_text = "\n\n".join([doc.page_content for doc in unique_docs])
        response = await llm.ainvoke(
            [{'role': 'user', 'content': f'帮我评估一下召回率:用户的问题{question},RAG检索结果:{context_text}'}])
        print(f'🤖 LLM RAG评估回复:{response.content}')
        # ==================================================
        # 5. 生成最终回答
        # ==================================================
        rag_system_prompt = f"""
        你是一个专业的医疗智能助手。请根据以下检索到的【参考信息】回答用户的问题。

        回答原则：
        1. 综合多条参考信息，逻辑清晰地回答。
        2. 如果参考信息中没有答案，请明确告知，不要瞎编。
        3. 语气亲切、专业。

        【参考信息】:
        {context_text}
        """

        final_messages = [
            SystemMessage(content=rag_system_prompt),
            *history_messages,
            HumanMessage(content=question)  # 给 LLM 看原始问题，保持对话流畅度
        ]

        response_stream = llm.astream(final_messages)

        final_answer = ""
        async for chunk in response_stream:
            content = chunk.content
            if content:
                final_answer += content
                yield f'data: {content}\n\n'

        # ==================================================
        # 6. 存入历史记录
        # ==================================================
        new_history = [
            {'role': 'user', 'content': question},
            {"role": "assistant", "content": final_answer}
        ]
        await redis_client.rpush(chat_message_list_key, *[json.dumps(m) for m in new_history])

        chat_message_hash_key = f'chat:message:hash:{user_id}:{session_id}'
        await redis_client.hset(chat_message_hash_key, mapping={
            "last_message": final_answer[:20]
        })

    # -------------------------------------------------------------------------
    # 辅助方法区域
    # -------------------------------------------------------------------------

    async def rewrite_query_based_on_history(self, question, history_messages) -> str:
        """
        【策略一实现】：基于历史记录重写问题
        """
        if not history_messages:
            return question

        prompt = """
        你是一个搜索优化专家。
        请根据【对话历史】和【用户的最新问题】，将用户的问题重写为一个**独立的、语义完整的**句子。
        例如：将"它有什么副作用"重写为"奥司他韦有什么副作用"。
        **只输出重写后的句子，不要解释。**
        """

        messages = [
            SystemMessage(content=prompt),
            HumanMessage(content=f"【对话历史】: {history_messages}\n【用户最新的问题】: {question}")
        ]

        # 使用 ainvoke 异步调用
        response = await llm.ainvoke(messages)
        return response.content.strip()

    async def generate_multi_queries(self, original_query: str) -> List[str]:
        """
        【策略二 & 三实现】：多角度扩展 + 问题分解
        """
        prompt = """
        你是一个AI搜索助手。为了更精准地回答用户的问题，请基于原始问题生成 3 个不同的搜索查询词。

        生成规则：
        1. **同义扩展**：包含相关的医学术语或别名（如"发烧"->"发热处理"）。
        2. **问题拆解**：如果问题复杂，拆解为子问题（如"甲流乙流区别"->"甲流症状"和"乙流症状"）。
        3. **保留原意**：必须包含原始问题的核心查询。

        请直接输出 3 行查询词，每行一个，不要带序号或解释。

        原始问题: {question}
        
        禁止：
            禁止修改用户原本的意思，比如：我嘴里面有点疼，怎么回事？禁止修改成：牙疼都有哪些症状？
        """

        messages = [SystemMessage(content=prompt.format(question=original_query))]

        response = await llm.ainvoke(messages)
        content = response.content.strip()

        # 解析结果，按行分割
        queries = [q.strip() for q in content.split('\n') if q.strip()]

        # 兜底：如果生成失败，至少保留原问题
        if not queries:
            return [original_query]

        # 把原始问题也加进去，确保万无一失
        if original_query not in queries:
            queries.insert(0, original_query)

        return queries[:4]  # 限制最多搜 4 次，防止太慢

    def _deduplicate_documents(self, documents: List[Document]) -> List[Document]:
        """
        文档去重工具：根据 page_content 去重
        """
        unique_docs = []
        seen_content = set()

        for doc in documents:
            # 取内容的前100个字符作为指纹，或者直接用整个content
            content_fingerprint = doc.page_content.strip()

            if content_fingerprint not in seen_content:
                seen_content.add(content_fingerprint)
                unique_docs.append(doc)

        return unique_docs


ai_service = AiService()
