"""
SQL查询工具集
提供安全的SQL执行、结果格式化等功能
"""

import duckdb
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import pandas as pd
import re
from datetime import datetime


class SQLExecutor:
    """
    安全的SQL执行器
    使用DuckDB执行SQL查询并返回结构化结果
    """

    # SQL关键字白名单 (只允许SELECT查询)
    ALLOWED_SQL_KEYWORDS = {
        'SELECT', 'FROM', 'WHERE', 'GROUP', 'BY', 'ORDER', 'LIMIT',
        'HAVING', 'AS', 'JOIN', 'ON', 'AND', 'OR', 'NOT', 'IN',
        'BETWEEN', 'LIKE', 'IS', 'NULL', 'DISTINCT', 'COUNT', 'SUM',
        'AVG', 'MIN', 'MAX', 'CAST', 'CASE', 'WHEN', 'THEN', 'ELSE',
        'END', 'UNION', 'EXCEPT', 'INTERSECT', 'WITH', 'OVER',
        'PARTITION', 'ROW_NUMBER', 'RANK', 'DENSE_RANK'
    }

    # 危险的SQL关键字黑名单
    FORBIDDEN_SQL_KEYWORDS = {
        'DROP', 'DELETE', 'INSERT', 'UPDATE', 'CREATE', 'ALTER',
        'TRUNCATE', 'REPLACE', 'MERGE', 'EXECUTE', 'EXEC'
    }

    def __init__(self, file_path: str, table_name: str = "data"):
        """
        初始化SQL执行器

        Args:
            file_path: 数据文件路径
            table_name: DuckDB中的表名 (默认: data)
        """
        self.file_path = file_path
        self.table_name = table_name
        self.conn = None

    def __enter__(self):
        """上下文管理器入口"""
        self._connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器退出"""
        self.close()

    def _connect(self):
        """建立DuckDB连接并加载数据"""
        if self.conn:
            return

        self.conn = duckdb.connect(':memory:')

        # 根据文件类型加载数据
        file_ext = Path(self.file_path).suffix.lower()

        try:
            if file_ext == '.csv':
                self.conn.execute(
                    f"CREATE TABLE {self.table_name} AS SELECT * FROM read_csv_auto('{self.file_path}')"
                )
            elif file_ext in ['.xlsx', '.xls']:
                # Excel文件:先用openpyxl读取,再导入DuckDB
                import openpyxl
                import csv
                import tempfile

                wb = openpyxl.load_workbook(self.file_path, read_only=True)
                ws = wb.active

                with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv', newline='', encoding='utf-8') as tmp:
                    csv_writer = csv.writer(tmp)
                    for row in ws.iter_rows(values_only=True):
                        csv_writer.writerow(row)
                    tmp_path = tmp.name

                self.conn.execute(
                    f"CREATE TABLE {self.table_name} AS SELECT * FROM read_csv_auto('{tmp_path}')"
                )
                Path(tmp_path).unlink()
                wb.close()

            elif file_ext == '.json':
                self.conn.execute(
                    f"CREATE TABLE {self.table_name} AS SELECT * FROM read_json_auto('{self.file_path}')"
                )
            elif file_ext == '.parquet':
                self.conn.execute(
                    f"CREATE TABLE {self.table_name} AS SELECT * FROM read_parquet('{self.file_path}')"
                )
            else:
                raise ValueError(f"Unsupported file type: {file_ext}")

        except Exception as e:
            if self.conn:
                self.conn.close()
                self.conn = None
            raise RuntimeError(f"Failed to load data: {str(e)}")

    def close(self):
        """关闭DuckDB连接"""
        if self.conn:
            self.conn.close()
            self.conn = None

    def validate_sql(self, sql: str) -> Tuple[bool, Optional[str]]:
        """
        验证SQL查询安全性

        检查项:
        1. 是否包含危险关键字 (DROP, DELETE, etc.)
        2. 是否只包含SELECT语句
        3. 基本SQL注入防护

        Args:
            sql: SQL查询语句

        Returns:
            (is_valid, error_message)
        """
        sql_upper = sql.upper()

        # 检查危险关键字
        for keyword in self.FORBIDDEN_SQL_KEYWORDS:
            if re.search(rf'\b{keyword}\b', sql_upper):
                return False, f"Forbidden SQL keyword detected: {keyword}"

        # 检查是否以SELECT开头
        if not sql_upper.strip().startswith('SELECT') and not sql_upper.strip().startswith('WITH'):
            return False, "Only SELECT queries are allowed"

        # 检查是否包含多个语句 (基本防护)
        if ';' in sql.rstrip(';'):
            return False, "Multiple SQL statements are not allowed"

        return True, None

    def execute(
        self,
        sql: str,
        max_rows: int = 1000
    ) -> Dict[str, Any]:
        """
        执行SQL查询

        Args:
            sql: SQL查询语句
            max_rows: 最大返回行数

        Returns:
            查询结果字典:
            {
                "success": bool,
                "data": List[Dict],  # 查询结果
                "columns": List[str],  # 列名
                "row_count": int,  # 实际行数
                "execution_time": float,  # 执行时间(秒)
                "sql": str,  # 执行的SQL
                "error": str  # 错误信息(如果有)
            }
        """
        # 验证SQL
        is_valid, error_msg = self.validate_sql(sql)
        if not is_valid:
            return {
                "success": False,
                "error": error_msg,
                "sql": sql
            }

        # 建立连接
        if not self.conn:
            self._connect()

        try:
            start_time = datetime.now()

            # 添加LIMIT限制 (如果没有)
            sql_with_limit = sql.strip()
            if not re.search(r'\bLIMIT\b', sql_with_limit, re.IGNORECASE):
                sql_with_limit += f" LIMIT {max_rows}"

            # 执行查询
            result = self.conn.execute(sql_with_limit).fetchdf()

            execution_time = (datetime.now() - start_time).total_seconds()

            # 转换为字典列表
            data = result.to_dict('records')

            # 处理特殊类型 (datetime, etc.)
            for row in data:
                for key, value in row.items():
                    if pd.isna(value):
                        row[key] = None
                    elif isinstance(value, (pd.Timestamp, datetime)):
                        row[key] = value.isoformat()
                    elif isinstance(value, (int, float)) and pd.isna(value):
                        row[key] = None

            return {
                "success": True,
                "data": data,
                "columns": result.columns.tolist(),
                "row_count": len(data),
                "execution_time": execution_time,
                "sql": sql_with_limit
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "sql": sql
            }

    def get_schema(self) -> List[Dict[str, str]]:
        """
        获取数据表schema

        Returns:
            Schema列表: [{"name": "col1", "type": "VARCHAR"}, ...]
        """
        if not self.conn:
            self._connect()

        try:
            schema_df = self.conn.execute(f"DESCRIBE {self.table_name}").fetchdf()
            return [
                {"name": row["column_name"], "type": row["column_type"]}
                for _, row in schema_df.iterrows()
            ]
        except Exception as e:
            raise RuntimeError(f"Failed to get schema: {str(e)}")

    def get_sample_data(self, limit: int = 5) -> pd.DataFrame:
        """
        获取样本数据

        Args:
            limit: 样本行数

        Returns:
            DataFrame样本数据
        """
        if not self.conn:
            self._connect()

        return self.conn.execute(f"SELECT * FROM {self.table_name} LIMIT {limit}").fetchdf()


class QueryResultFormatter:
    """
    查询结果格式化器
    将查询结果转换为不同格式
    """

    @staticmethod
    def to_markdown_table(
        data: List[Dict[str, Any]],
        columns: Optional[List[str]] = None,
        max_rows: int = 20
    ) -> str:
        """
        转换为Markdown表格

        Args:
            data: 查询结果数据
            columns: 列名列表 (可选,从数据推断)
            max_rows: 最大显示行数

        Returns:
            Markdown格式的表格字符串
        """
        if not data:
            return "*No results*"

        # 推断列名
        if columns is None:
            columns = list(data[0].keys())

        # 限制行数
        display_data = data[:max_rows]

        # 构建表头
        header = "| " + " | ".join(columns) + " |"
        separator = "| " + " | ".join(["---"] * len(columns)) + " |"

        # 构建数据行
        rows = []
        for row in display_data:
            row_str = "| " + " | ".join(
                str(row.get(col, "")) for col in columns
            ) + " |"
            rows.append(row_str)

        # 组合
        table = "\n".join([header, separator] + rows)

        # 添加省略提示
        if len(data) > max_rows:
            table += f"\n\n*Showing {max_rows} of {len(data)} rows*"

        return table

    @staticmethod
    def to_summary(
        data: List[Dict[str, Any]],
        columns: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        生成数据摘要

        Args:
            data: 查询结果数据
            columns: 列名列表

        Returns:
            摘要字典
        """
        if not data:
            return {
                "row_count": 0,
                "column_count": 0,
                "columns": []
            }

        if columns is None:
            columns = list(data[0].keys())

        # 转为DataFrame便于统计
        df = pd.DataFrame(data)

        summary = {
            "row_count": len(data),
            "column_count": len(columns),
            "columns": columns,
            "column_stats": {}
        }

        # 每列的统计
        for col in columns:
            col_data = df[col]
            stats = {
                "dtype": str(col_data.dtype),
                "non_null_count": int(col_data.count()),
                "null_count": int(col_data.isna().sum()),
                "unique_count": int(col_data.nunique())
            }

            # 如果是数值类型,添加统计信息
            if pd.api.types.is_numeric_dtype(col_data):
                stats.update({
                    "min": float(col_data.min()) if not col_data.empty else None,
                    "max": float(col_data.max()) if not col_data.empty else None,
                    "mean": float(col_data.mean()) if not col_data.empty else None,
                    "median": float(col_data.median()) if not col_data.empty else None
                })

            summary["column_stats"][col] = stats

        return summary


class SchemaRetriever:
    """
    Schema检索器
    从Dataset模型中获取schema信息供LLM使用
    """

    @staticmethod
    def format_schema_for_llm(schema_json: List[Dict[str, Any]]) -> str:
        """
        将schema格式化为LLM友好的格式

        Args:
            schema_json: Dataset.schema_json字段

        Returns:
            格式化的schema字符串
        """
        if not schema_json:
            return "No schema available"

        lines = []
        for col in schema_json:
            line = f"- {col['name']} ({col['dtype']})"

            # 添加统计信息
            if col.get('non_null_count'):
                line += f" - {col['non_null_count']} non-null"
            if col.get('unique_count'):
                line += f", {col['unique_count']} unique"
            if col.get('min') is not None and col.get('max') is not None:
                line += f", range: [{col['min']}, {col['max']}]"

            lines.append(line)

        return "\n".join(lines)

    @staticmethod
    def get_column_names(schema_json: List[Dict[str, Any]]) -> List[str]:
        """
        提取列名列表

        Args:
            schema_json: Dataset.schema_json字段

        Returns:
            列名列表
        """
        return [col['name'] for col in schema_json]

    @staticmethod
    def get_numeric_columns(schema_json: List[Dict[str, Any]]) -> List[str]:
        """
        提取数值类型列

        Args:
            schema_json: Dataset.schema_json字段

        Returns:
            数值列名列表
        """
        numeric_types = ['BIGINT', 'INTEGER', 'SMALLINT', 'TINYINT',
                        'DOUBLE', 'FLOAT', 'DECIMAL', 'NUMERIC', 'HUGEINT']

        numeric_cols = []
        for col in schema_json:
            if any(num_type in col['dtype'].upper() for num_type in numeric_types):
                numeric_cols.append(col['name'])

        return numeric_cols
