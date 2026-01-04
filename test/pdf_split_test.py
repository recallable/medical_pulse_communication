import glob
import os
from typing import List

from langchain_community.embeddings import DashScopeEmbeddings
from langchain_core.documents import Document
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_postgres import PGVector
from langchain_text_splitters import MarkdownHeaderTextSplitter
from llama_parse import LlamaParse, ResultType

from core.ai import llm

# ================= 1. 配置区域 =================
# API Keys
LLAMA_CLOUD_API_KEY = 'llx-aoa7Ko4Qc7VRuHooMqxWbOhRJZq3pHwNH67QlzL9gMOdYJPi'
# 确保环境变量中有 DASHSCOPE_API_KEY，或者直接填在这里
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY")

# 目录配置
INPUT_DIR = "../docs"  # PDF 所在的根目录
MD_OUTPUT_DIR = "../docs_markdown"  # 解析后的 Markdown 存放目录 (自动创建)

# 数据库连接
DB_CONNECTION = "postgresql+psycopg2://postgres:121518@localhost:5432/rag_db"
COLLECTION_NAME = "h1n1_knowledge_base"

# ================= 2. 初始化全局组件 =================
# (这些组件只需要初始化一次，不需要在循环里反复创建)

# 初始化 LlamaParse
parser = LlamaParse(
    result_type=ResultType.MD,
    api_key=LLAMA_CLOUD_API_KEY,
    language="ch_sim",
    system_prompt="""
    你是一个文档重构与转换专家。你的任务是将PDF内容转换为语义连贯、结构清晰的Markdown文档。
    请严格执行以下“清洗-重构-格式化”三步流程：

    1. 【第一步：去除噪音与修复分页（最高优先级）】
       - **识别假标题（页眉噪音）**：文档中重复出现的“一、甲流简介”、“甲型H1N1流感医疗知识库”等通常是页眉。如果这些文本出现在段落中间，或者切断了子章节（如出现在“3.1 核心病因”和其正文之间），**必须将其视为噪音直接删除**，严禁保留为标题。
       - **跨页语义合并**：当遇到子标题（如“3.1 核心病因”）后紧接页眉噪音时，请忽略页眉，将下一页的正文直接拼接到该子标题下方。确保“3.1”的内容不为空，保持语义连贯。
       - **去除元数据**：严禁输出“**标题：**”、“**正文：**”、“”等标签；去除所有页码信息（如“PAGE 1”）。

    2. 【第二步：建立标题层级】
       - 仅对**真正的章节起始**应用标题格式：
         - 中文数字开头的章节（如“一、甲流简介”）：使用一级标题 "# "。
         - 数字编号的小节（如“2.1 病原学特征”）：使用二级标题 "## "。
         - 其他加粗小标题：使用三级标题 "### "。

    3. 【第三步：格式化内容】
       - **表格**：必须将表格转换为标准的 Markdown 表格语法，确保数据不丢失。
       - **正文**：保持段落完整，移除多余的换行符。

    目标：输出一份可以直接用于RAG检索的纯净Markdown，不要包含任何解释性文字。
    """
)

# 初始化切分器
headers_to_split_on = [
    ("#", "Chapter"),
    ("##", "Section"),
    ("###", "Subsection"),
]
markdown_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on, strip_headers=False)

# 初始化 Embeddings
embeddings = DashScopeEmbeddings(model="text-embedding-v1", dashscope_api_key=DASHSCOPE_API_KEY)

# 初始化 VectorStore
vector_store = PGVector(
    embeddings=embeddings,
    collection_name=COLLECTION_NAME,
    connection=DB_CONNECTION,
    use_jsonb=True,
)


# ================= 3. 核心处理逻辑 =================

def process_directory(directory_path):
    # 1. 递归查找所有 .pdf 文件
    # glob 模式 '**/*.pdf' 配合 recursive=True 可以穿透子目录
    pdf_files = glob.glob(os.path.join(directory_path, "**/*.pdf"), recursive=True)

    print(f"📂 扫描目录: {directory_path}")
    print(f"📄 发现 PDF 文件数: {len(pdf_files)}")

    # 确保输出目录存在
    if not os.path.exists(MD_OUTPUT_DIR):
        os.makedirs(MD_OUTPUT_DIR)

    # 2. 循环处理每个文件
    for index, pdf_path in enumerate(pdf_files):
        try:
            filename = os.path.basename(pdf_path)
            print(f"\n[{index + 1}/{len(pdf_files)}] 🚀 正在处理: {filename}")

            # --- A. 解析 PDF (LlamaParse) ---
            documents = parser.load_data(pdf_path)
            if not documents:
                print(f"⚠️ 跳过: {filename} 解析结果为空")
                continue

            raw_markdown = "\n\n".join([doc.text for doc in documents])

            # --- B. 保存 Markdown 备份 (可选) ---
            # 保持文件名一致，只改后缀
            md_filename = f"{os.path.splitext(filename)[0]}.md"
            md_save_path = os.path.join(MD_OUTPUT_DIR, md_filename)

            with open(md_save_path, "w", encoding="utf-8") as f:
                f.write(raw_markdown)
            print(f"   💾 Markdown 已保存至: {md_save_path}")

            # --- C. 切分文本 ---
            splits = markdown_splitter.split_text(raw_markdown)

            # --- D. 注入元数据 (关键步骤！) ---
            # 这一点非常重要：我们需要给每个切片打上标签，知道它来自哪个文件
            for split in splits:
                # 保留原有的标题元数据，并增加来源信息
                split.metadata["source"] = filename
                split.metadata["file_path"] = pdf_path

            print(f"   ✂️ 切分得到 {len(splits)} 个片段")

            # --- E. 向量化并存入数据库 ---
            # 批量插入当前文件的所有切片
            vector_store.add_documents(splits)
            print(f"   ✅ {filename} 入库成功！")

        except Exception as e:
            # 捕获异常，防止一个文件报错导致整个程序停止
            print(f"❌ 处理文件 {filename} 时发生错误: {e}")
            continue


def process_single_markdown(file_path):
    """
    读取单个 Markdown 文件并存入向量数据库
    """
    # 0. 检查文件是否存在
    if not os.path.exists(file_path):
        print(f"❌ 错误: 文件不存在 -> {file_path}")
        return

    try:
        filename = os.path.basename(file_path)
        print(f"\n🚀 正在处理单文件: {filename}")

        # 1. 读取 Markdown 文件内容
        with open(file_path, "r", encoding="utf-8") as f:
            raw_markdown = f.read()

        print(f"   📖 读取成功，字符数: {len(raw_markdown)}")

        # 2. 切分文本 (复用全局定义的 markdown_splitter)
        splits = markdown_splitter.split_text(raw_markdown)

        # 3. 注入元数据 (关键步骤)
        for split in splits:
            # 记录来源，方便后续检索时溯源
            split.metadata["source"] = filename
            split.metadata["file_path"] = file_path

        print(f"   ✂️ 切分得到 {len(splits)} 个片段")

        # 4. 向量化并存入数据库 (复用全局定义的 vector_store)
        if splits:
            vector_store.add_documents(splits)
            print(f"   ✅ {filename} 入库成功！")
        else:
            print(f"   ⚠️ 警告: 文件内容为空或未能切分出任何片段")

    except Exception as e:
        print(f"❌ 处理文件 {filename} 时发生错误: {e}")


def chat(question: str):
    """
    AI 聊天接口 (融合三种 RAG 策略)
    """

    # ==================================================
    # 3. 【策略二 & 三：多路扩展与分解】 (Expansion & Decomposition)
    # 目的：生成多个搜索视角和子问题
    # ==================================================
    # 这一步会生成一个列表，例如 ["甲流治疗方案", "儿童甲流用药", "甲流发烧护理"]
    queries_to_search = generate_multi_queries(question)
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
    unique_docs = deduplicate_documents(all_docs)
    print(f"📚 [最终] 检索到 {len(unique_docs)} 个不重复片段")

    # 构建上下文
    context_text = "\n\n".join([doc.page_content for doc in unique_docs])
    messages = [
        SystemMessage(content='你是一个Rag评估专家, 请根据用户的问题和RAG检索结果,评估一下召回率。'),
        HumanMessage(content=f'用户的问题: {question}, RAG检索结果: {context_text}')
    ]
    response = llm.invoke(messages)
    print(response.content)
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
        HumanMessage(content=question)  # 给 LLM 看原始问题，保持对话流畅度
    ]

    response = llm.invoke(final_messages)

    return response.content


# -------------------------------------------------------------------------
# 辅助方法区域
# -------------------------------------------------------------------------

def generate_multi_queries(original_query: str) -> List[str]:
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

    response = llm.invoke(messages)
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


def deduplicate_documents(documents: List[Document]) -> List[Document]:
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


# ================= 4. 执行 =================
if __name__ == "__main__":
    # process_directory(INPUT_DIR)
    # single_md_file = "../docs_markdown/儿童发热家庭护理手册.md"

    # docs_markdown_list = [
    #     '../docs_markdown/上呼吸道感染医疗知识库.md',
    #     '../docs_markdown/下呼吸道感染医疗知识库.md',
    #     '../docs_markdown/代谢综合征医疗知识库.md',
    #     '../docs_markdown/关节疾病医疗知识库.md',
    #     '../docs_markdown/内分泌与代谢性疾病医疗知识库.md',
    #     '../docs_markdown/冠心病医疗知识库.md',
    #     '../docs_markdown/尿路疾病医疗知识库.md',
    #     '../docs_markdown/常见传染病医疗知识库.md',
    #     '../docs_markdown/心力衰竭医疗知识库.md',
    #     '../docs_markdown/心律失常医疗知识库.md',
    #     '../docs_markdown/心血管系统疾病医疗知识库.md',
    #     '../docs_markdown/慢性呼吸系统疾病医疗知识库.md',
    #     '../docs_markdown/泌尿系统疾病医疗知识库.md',
    #     '../docs_markdown/消化系统疾病医疗知识库.md',
    #     '../docs_markdown/甲状腺疾病医疗知识库.md',
    #     '../docs_markdown/神经系统疾病医疗知识库.md',
    #     '../docs_markdown/神经退行性疾病医疗知识库.md',
    #     '../docs_markdown/精神心理疾病医疗知识库.md',
    #     '../docs_markdown/糖尿病医疗知识库.md',
    #     '../docs_markdown/肝胆胰疾病医疗知识库.md',
    #     '../docs_markdown/肾脏疾病医疗知识库.md',
    #     '../docs_markdown/胃肠道疾病医疗知识库.md',
    #     '../docs_markdown/脑血管疾病医疗知识库.md',
    #     '../docs_markdown/骨骼疾病医疗知识库.md',
    #     '../docs_markdown/骨骼肌肉系统疾病医疗知识库.md',
    #     '../docs_markdown/高血压医疗知识库.md',
    # ]
    # for idx in trange(len(docs_markdown_list)):
    #     process_single_markdown(docs_markdown_list[idx])
    # process_single_markdown(single_md_file)
    query = '怎么判断自己有没有精神病?'
    chat(query)
    # results = vector_store.similarity_search(query, k=3)
    # for i, doc in enumerate(results):
    #     print(f"   --- 结果 {i + 1} ---")
    #     print(f"   [来源]: {doc.metadata.get('source', '未知')}")
    #     print(f"   [内容]: {doc.page_content}")  # 只打印前100字预览
    #
    # llm = init_chat_model(
    #     model='qwen-flash',
    #     model_provider='openai',
    #     api_key=os.getenv('OPENAI_API_KEY'),
    # )
    # response = llm.invoke(f"评估一下召回率: 用户的问题:{query}, RAG检索的数据:{results}")
    # print(response.content)
    # print("\n🎉 所有任务处理完毕！")
