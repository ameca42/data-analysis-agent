"""
LLM客户端工具模块
提供统一的LLM调用接口,支持OpenAI API兼容的服务
"""

from typing import List, Dict, Any, Optional
import httpx
import json
from backend.config import get_settings

settings = get_settings()


class LLMClient:
    """
    LLM客户端封装类

    支持:
    - OpenAI API
    - 兼容OpenAI API的本地模型 (Ollama, vLLM, etc.)
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model_name: Optional[str] = None,
        timeout: float = 60.0
    ):
        """
        初始化LLM客户端

        Args:
            api_key: API密钥 (默认从配置读取)
            base_url: API基础URL (默认从配置读取)
            model_name: 模型名称 (默认从配置读取)
            timeout: 请求超时时间(秒)
        """
        self.api_key = api_key or settings.llm_api_key
        self.base_url = (base_url or settings.llm_base_url).rstrip('/')
        self.model_name = model_name or settings.llm_model_name
        self.timeout = timeout

        # 构建完整的API端点
        self.chat_endpoint = f"{self.base_url}/chat/completions"

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.1,
        max_tokens: Optional[int] = None,
        stop: Optional[List[str]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        调用LLM聊天补全API

        Args:
            messages: 消息列表 [{"role": "user", "content": "..."}]
            temperature: 温度参数 (0.0-2.0, 越低越确定)
            max_tokens: 最大生成token数
            stop: 停止词列表
            **kwargs: 其他模型参数

        Returns:
            API响应字典

        Raises:
            httpx.HTTPError: HTTP请求失败
            json.JSONDecodeError: 响应解析失败
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model_name,
            "messages": messages,
            "temperature": temperature,
            **kwargs
        }

        if max_tokens:
            payload["max_tokens"] = max_tokens
        if stop:
            payload["stop"] = stop

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                self.chat_endpoint,
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            return response.json()

    async def extract_content(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> str:
        """
        提取LLM响应的文本内容

        Args:
            messages: 消息列表
            **kwargs: chat_completion参数

        Returns:
            LLM生成的文本内容
        """
        response = await self.chat_completion(messages, **kwargs)
        return response["choices"][0]["message"]["content"]


class NL2SQLConverter:
    """
    自然语言转SQL转换器
    使用LLM将用户的自然语言问题转换为SQL查询
    """

    def __init__(self, llm_client: Optional[LLMClient] = None):
        """
        初始化转换器

        Args:
            llm_client: LLM客户端实例 (可选,默认创建新实例)
        """
        self.llm_client = llm_client or LLMClient()

    def build_nl2sql_prompt(
        self,
        question: str,
        schema: List[Dict[str, Any]],
        table_name: str = "data",
        examples: Optional[List[Dict[str, str]]] = None
    ) -> List[Dict[str, str]]:
        """
        构建NL2SQL提示词

        Args:
            question: 用户的自然语言问题
            schema: 数据表schema (从Dataset.schema_json获取)
            table_name: 表名 (DuckDB中默认为'data')
            examples: Few-shot示例 (可选)

        Returns:
            消息列表
        """
        # 格式化schema信息
        schema_str = "Table: {}\nColumns:\n".format(table_name)
        for col in schema:
            col_desc = f"- {col['name']} ({col['dtype']})"
            if col.get('non_null_count'):
                col_desc += f" - {col['non_null_count']} non-null values"
            if col.get('unique_count'):
                col_desc += f", {col['unique_count']} unique"
            if col.get('min') is not None:
                col_desc += f", range: [{col['min']:.2f}, {col['max']:.2f}]"
            schema_str += col_desc + "\n"

        # 构建系统提示
        system_prompt = f"""You are an expert SQL query generator for DuckDB.

Task: Convert natural language questions to SQL queries.

{schema_str}

Requirements:
1. Generate ONLY the SQL query, no explanations
2. Use double quotes for column names with spaces: "column name"
3. Always use WHERE clause to filter NULL values when appropriate
4. Use appropriate aggregation functions (COUNT, SUM, AVG, etc.)
5. Add ORDER BY and LIMIT when relevant
6. Return the query in a single line
7. Do NOT include semicolon at the end

Examples:
Q: How many rows are there?
A: SELECT COUNT(*) as row_count FROM data

Q: What's the average of sales column?
A: SELECT AVG("sales") as avg_sales FROM data WHERE "sales" IS NOT NULL

Q: Show me top 5 categories by count
A: SELECT category, COUNT(*) as count FROM data WHERE category IS NOT NULL GROUP BY category ORDER BY count DESC LIMIT 5"""

        messages = [
            {"role": "system", "content": system_prompt}
        ]

        # 添加Few-shot示例
        if examples:
            for example in examples:
                messages.append({"role": "user", "content": example["question"]})
                messages.append({"role": "assistant", "content": example["sql"]})

        # 添加用户问题
        messages.append({"role": "user", "content": question})

        return messages

    async def convert(
        self,
        question: str,
        schema: List[Dict[str, Any]],
        table_name: str = "data"
    ) -> str:
        """
        转换自然语言问题为SQL查询

        Args:
            question: 用户问题
            schema: 数据表schema
            table_name: 表名

        Returns:
            生成的SQL查询语句
        """
        messages = self.build_nl2sql_prompt(question, schema, table_name)

        sql_query = await self.llm_client.extract_content(
            messages,
            temperature=0.1,  # 低温度保证确定性
            max_tokens=500
        )

        # 清理SQL查询
        sql_query = sql_query.strip()

        # 移除可能的markdown代码块标记
        if sql_query.startswith("```sql"):
            sql_query = sql_query[6:]
        if sql_query.startswith("```"):
            sql_query = sql_query[3:]
        if sql_query.endswith("```"):
            sql_query = sql_query[:-3]

        sql_query = sql_query.strip()

        # 移除末尾分号
        if sql_query.endswith(";"):
            sql_query = sql_query[:-1]

        return sql_query


class QueryExplainer:
    """
    SQL查询结果解释器
    使用LLM将查询结果转换为自然语言解释
    """

    def __init__(self, llm_client: Optional[LLMClient] = None):
        """
        初始化解释器

        Args:
            llm_client: LLM客户端实例
        """
        self.llm_client = llm_client or LLMClient()

    async def explain_results(
        self,
        question: str,
        sql_query: str,
        results: List[Dict[str, Any]],
        max_rows_to_show: int = 10
    ) -> str:
        """
        解释查询结果

        Args:
            question: 原始问题
            sql_query: 执行的SQL查询
            results: 查询结果 (字典列表)
            max_rows_to_show: 最多显示的行数

        Returns:
            自然语言解释
        """
        # 限制结果行数
        results_preview = results[:max_rows_to_show]

        # 格式化结果
        results_str = json.dumps(results_preview, indent=2, ensure_ascii=False)
        if len(results) > max_rows_to_show:
            results_str += f"\n... ({len(results) - max_rows_to_show} more rows)"

        prompt = f"""You are a data analyst assistant. Explain the SQL query results in natural language.

User Question: {question}

SQL Query Executed:
{sql_query}

Query Results:
{results_str}

Total Rows: {len(results)}

Task: Provide a clear, concise explanation of the results in 2-3 sentences. Focus on answering the user's question directly.

Response format:
- Start with a direct answer to the question
- Include key numbers and insights
- Keep it conversational and easy to understand"""

        messages = [
            {"role": "user", "content": prompt}
        ]

        explanation = await self.llm_client.extract_content(
            messages,
            temperature=0.3,
            max_tokens=300
        )

        return explanation.strip()


# 创建全局实例 (可选)
def get_llm_client() -> LLMClient:
    """获取LLM客户端实例"""
    return LLMClient()


def get_nl2sql_converter() -> NL2SQLConverter:
    """获取NL2SQL转换器实例"""
    return NL2SQLConverter()


def get_query_explainer() -> QueryExplainer:
    """获取查询解释器实例"""
    return QueryExplainer()
