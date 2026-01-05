from elasticsearch import AsyncElasticsearch
# 引入这两个核心类
from elasticsearch.dsl import Search, Q

from models.schemas.medical_record import SearchRequest


class AsyncMedicalSearchEngine:
    def __init__(self, es_host: str = "http://localhost:9200", index_name: str = "medical_records"):
        self.es = AsyncElasticsearch(es_host)
        self.index = index_name

    async def close(self):
        await self.es.close()

    async def search(self, req: SearchRequest):
        # ==========================================
        # 1. 使用 Search 对象作为"画板"
        # ==========================================
        s = Search()

        # ==========================================
        # 2. 构建 Query (Must) - 关键词搜索
        # ==========================================
        if req.keyword:
            # Q 是 Query 的缩写，Q("查询类型", 参数...)
            # 相当于生成了 {"multi_match": ...}
            q_keyword = Q("multi_match",
                          query=req.keyword,
                          fields=["disease_name^3", "symptoms^2", "extend_info.*"],
                          type="best_fields")
            s = s.query(q_keyword)
        else:
            s = s.query("match_all")

        # ==========================================
        # 3. 构建 Filter (结构化筛选)
        # ==========================================
        # elasticsearch-dsl 的 filter 方法会自动合并到 bool filter 中
        if req.filters:
            f = req.filters

            # 精确匹配 Term
            if f.department:
                s = s.filter("term", department=f.department)

            if f.doctor_name:
                s = s.filter("term", doctor_name=f.doctor_name)

            # 范围查询 Range
            if f.min_age or f.max_age:
                range_params = {}
                if f.min_age: range_params['gte'] = f.min_age
                if f.max_age: range_params['lte'] = f.max_age
                s = s.filter("range", patient_age=range_params)

            # JSONB 动态字段
            if f.extend_key and f.extend_value:
                # 动态 key 需要用 **kwargs 方式传参
                s = s.filter("match", **{f"extend_info.{f.extend_key}": f.extend_value})

        # ==========================================
        # 4. 高亮 (Highlight)
        # ==========================================
        # 链式调用，非常直观
        s = s.highlight("disease_name", "symptoms")
        s = s.highlight_options(pre_tags=["<em style='color:red'>"], post_tags=["</em>"])

        # ==========================================
        # 5. 分页 & 导出 & 异步执行
        # ==========================================
        # 设置分页 (from/size)
        s = s[(req.page - 1) * req.size: req.page * req.size]

        # 🚀 关键一步：to_dict()
        # 把构建好的优雅对象，瞬间变成 ES 能看懂的复杂 JSON
        query_body = s.to_dict()

        # 打印看看生成的 JSON (调试用)
        # import json
        # print(json.dumps(query_body, ensure_ascii=False, indent=2))

        # 使用异步客户端发送请求
        response = await self.es.search(index=self.index, body=query_body)

        # ... (后续的结果解析逻辑和之前一样) ...
        return self._format_response(response)

    def _format_response(self, response):
        # 把之前的格式化逻辑挪到这里
        hits = response["hits"]["hits"]
        results = []
        for hit in hits:
            source = hit["_source"]
            hl = hit.get("highlight", {})
            results.append({
                "id": source.get("id"),
                "record_no": source.get("record_no"),
                "patient_name": source.get("patient_name"),
                "age": source.get("patient_age"),
                "department": source.get("department"),
                "score": hit["_score"],
                "highlight_disease": hl.get("disease_name", [source.get("disease_name")])[0],
                "highlight_symptoms": hl.get("symptoms", [source.get("symptoms")])[0],
                "raw_data": source
            })
        return {
            "total": response["hits"]["total"]["value"],
            "took_ms": response["took"],
            "data": results
        }

es  = AsyncMedicalSearchEngine()
