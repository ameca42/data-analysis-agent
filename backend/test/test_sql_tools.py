"""
SQL查询工具集测试脚本
快速验证核心功能
"""

import asyncio
import sys
from pathlib import Path

# 添加backend到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.utils.sql_tools import SQLExecutor, SchemaRetriever


def test_sql_validation():
    """测试SQL验证功能"""
    print("\n" + "="*60)
    print("测试1: SQL安全验证")
    print("="*60)

    # 创建一个临时执行器
    executor = SQLExecutor.__new__(SQLExecutor)
    executor.table_name = "data"

    # 测试用例
    test_cases = [
        ("SELECT * FROM data", True, "基本SELECT查询"),
        ("SELECT name, age FROM data WHERE age > 18", True, "带WHERE条件"),
        ("SELECT COUNT(*) FROM data GROUP BY category", True, "聚合查询"),
        ("DROP TABLE data", False, "危险的DROP操作"),
        ("DELETE FROM data WHERE id=1", False, "危险的DELETE操作"),
        ("SELECT * FROM data; DROP TABLE users", False, "SQL注入尝试"),
        ("UPDATE data SET name='test'", False, "危险的UPDATE操作"),
    ]

    passed = 0
    failed = 0

    for sql, should_pass, description in test_cases:
        is_valid, error = executor.validate_sql(sql)
        status = "✅ PASS" if is_valid == should_pass else "❌ FAIL"

        if is_valid == should_pass:
            passed += 1
        else:
            failed += 1

        print(f"\n{status} - {description}")
        print(f"SQL: {sql}")
        print(f"Expected: {'Valid' if should_pass else 'Invalid'}, Got: {'Valid' if is_valid else 'Invalid'}")
        if error:
            print(f"Error: {error}")

    print(f"\n{'='*60}")
    print(f"测试结果: {passed} passed, {failed} failed")
    print(f"{'='*60}")

    return failed == 0


def test_schema_retriever():
    """测试Schema检索功能"""
    print("\n" + "="*60)
    print("测试2: Schema检索")
    print("="*60)

    # 模拟Dataset.schema_json
    mock_schema = [
        {
            "name": "product",
            "dtype": "VARCHAR",
            "non_null_count": 1000,
            "unique_count": 50
        },
        {
            "name": "sales",
            "dtype": "DOUBLE",
            "non_null_count": 995,
            "unique_count": 500,
            "min": 100.0,
            "max": 5000.0,
            "mean": 1500.0
        },
        {
            "name": "quantity",
            "dtype": "INTEGER",
            "non_null_count": 1000,
            "unique_count": 100,
            "min": 1,
            "max": 100
        },
        {
            "name": "category",
            "dtype": "VARCHAR",
            "non_null_count": 980,
            "unique_count": 10
        }
    ]

    # 测试列名提取
    columns = SchemaRetriever.get_column_names(mock_schema)
    print(f"\n✅ 所有列名: {columns}")
    assert columns == ["product", "sales", "quantity", "category"]

    # 测试数值列提取
    numeric_cols = SchemaRetriever.get_numeric_columns(mock_schema)
    print(f"✅ 数值列: {numeric_cols}")
    assert "sales" in numeric_cols
    assert "quantity" in numeric_cols
    assert "product" not in numeric_cols

    # 测试LLM格式化
    llm_format = SchemaRetriever.format_schema_for_llm(mock_schema)
    print(f"\n✅ LLM格式化Schema:\n{llm_format}")

    print(f"\n{'='*60}")
    print("Schema检索测试通过!")
    print(f"{'='*60}")

    return True


async def test_llm_client():
    """测试LLM客户端 (需要配置API密钥)"""
    print("\n" + "="*60)
    print("测试3: LLM客户端")
    print("="*60)

    try:
        from backend.utils.llm_client import LLMClient
        from backend.config import get_settings

        settings = get_settings()

        # 检查API密钥是否配置
        if not settings.llm_api_key or settings.llm_api_key == "your_api_key_here":
            print("⚠️  跳过LLM测试: 未配置LLM_API_KEY")
            print("请在.env文件中设置LLM_API_KEY, LLM_BASE_URL, LLM_MODEL_NAME")
            return True

        print(f"✅ LLM配置:")
        print(f"   Base URL: {settings.llm_base_url}")
        print(f"   Model: {settings.llm_model_name}")

        # 创建客户端
        client = LLMClient()

        # 测试简单对话
        print(f"\n🔄 测试LLM调用...")
        messages = [
            {"role": "user", "content": "Say 'Hello, I am working!' in one sentence."}
        ]

        try:
            response = await client.chat_completion(messages, max_tokens=50)
            content = response["choices"][0]["message"]["content"]
            print(f"✅ LLM响应: {content}")

            print(f"\n{'='*60}")
            print("LLM客户端测试通过!")
            print(f"{'='*60}")
            return True

        except Exception as e:
            print(f"❌ LLM调用失败: {str(e)}")
            print("请检查:")
            print("1. LLM_API_KEY是否正确")
            print("2. LLM_BASE_URL是否可访问")
            print("3. LLM_MODEL_NAME是否存在")
            return False

    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_nl2sql():
    """测试NL2SQL转换 (需要LLM)"""
    print("\n" + "="*60)
    print("测试4: NL2SQL转换")
    print("="*60)

    try:
        from backend.utils.llm_client import NL2SQLConverter
        from backend.config import get_settings

        settings = get_settings()

        if not settings.llm_api_key or settings.llm_api_key == "your_api_key_here":
            print("⚠️  跳过NL2SQL测试: 未配置LLM_API_KEY")
            return True

        # 模拟schema
        mock_schema = [
            {"name": "product", "dtype": "VARCHAR", "non_null_count": 1000, "unique_count": 50},
            {"name": "sales", "dtype": "DOUBLE", "non_null_count": 1000, "min": 100, "max": 5000},
            {"name": "category", "dtype": "VARCHAR", "non_null_count": 980, "unique_count": 10}
        ]

        converter = NL2SQLConverter()

        # 测试用例
        test_questions = [
            "数据集有多少行?",
            "销售额的平均值是多少?",
            "每个类别的总销售额?"
        ]

        for question in test_questions:
            print(f"\n🔄 问题: {question}")
            try:
                sql = await converter.convert(question, mock_schema)
                print(f"✅ 生成的SQL: {sql}")
            except Exception as e:
                print(f"❌ 转换失败: {str(e)}")

        print(f"\n{'='*60}")
        print("NL2SQL测试完成!")
        print(f"{'='*60}")
        return True

    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """运行所有测试"""
    print("\n" + "🧪 SQL查询工具集测试套件" + "\n")

    results = []

    # 测试1: SQL验证
    results.append(("SQL验证", test_sql_validation()))

    # 测试2: Schema检索
    results.append(("Schema检索", test_schema_retriever()))

    # 测试3 & 4: 异步测试
    async def run_async_tests():
        llm_result = await test_llm_client()
        nl2sql_result = await test_nl2sql()
        return llm_result, nl2sql_result

    llm_result, nl2sql_result = asyncio.run(run_async_tests())
    results.append(("LLM客户端", llm_result))
    results.append(("NL2SQL转换", nl2sql_result))

    # 总结
    print("\n" + "="*60)
    print("📊 测试总结")
    print("="*60)

    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test_name}")

    total = len(results)
    passed_count = sum(1 for _, p in results if p)
    failed_count = total - passed_count

    print(f"\n总计: {passed_count}/{total} 通过")

    if failed_count == 0:
        print("\n🎉 所有测试通过!")
    else:
        print(f"\n⚠️  {failed_count} 个测试失败")

    print("="*60)

    return failed_count == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
