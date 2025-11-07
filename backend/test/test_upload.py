"""
测试文件上传功能的脚本

使用方法:
1. 启动服务器: uvicorn backend.main:app --reload
2. 运行此脚本: python test_upload.py
"""

import requests
import pandas as pd
import os

# API 基础 URL
BASE_URL = "http://localhost:8000"


def create_sample_csv():
    """创建一个示例 CSV 文件用于测试"""
    data = {
        'id': [1, 2, 3, 4, 5],
        'name': ['Alice', 'Bob', 'Charlie', 'David', 'Eve'],
        'age': [25, 30, 35, 28, 32],
        'salary': [50000, 60000, 75000, 55000, 65000],
        'department': ['IT', 'HR', 'IT', 'Sales', 'HR']
    }
    df = pd.DataFrame(data)
    df.to_csv('test_data.csv', index=False)
    print("✓ 已创建测试文件: test_data.csv")
    return 'test_data.csv'


def test_upload_file(file_path: str):
    """测试文件上传"""
    print(f"\n开始上传文件: {file_path}")

    with open(file_path, 'rb') as f:
        files = {'file': (os.path.basename(file_path), f, 'text/csv')}
        data = {
            'name': '员工数据示例',
            'description': '这是一个包含员工信息的测试数据集'
        }

        response = requests.post(
            f"{BASE_URL}/upload/",
            files=files,
            data=data
        )

    if response.status_code == 200:
        result = response.json()
        print("✓ 上传成功！")
        print(f"  数据集 ID: {result['id']}")
        print(f"  数据集名称: {result['name']}")
        print(f"  文件大小: {result['file_size']} bytes")
        print(f"  行数: {result['row_count']}")
        print(f"  列数: {len(result['schema_json'])}")
        print("\n  列信息:")
        for col in result['schema_json']:
            print(f"    - {col['name']}: {col['dtype']} (非空: {col['non_null_count']}, 唯一值: {col['unique_count']})")
        return result['id']
    else:
        print(f"✗ 上传失败: {response.status_code}")
        print(f"  错误信息: {response.text}")
        return None


def test_list_datasets():
    """测试获取数据集列表"""
    print("\n获取数据集列表:")
    response = requests.get(f"{BASE_URL}/upload/datasets")

    if response.status_code == 200:
        datasets = response.json()
        print(f"✓ 共有 {len(datasets)} 个数据集")
        for ds in datasets:
            print(f"  - [{ds['id']}] {ds['name']} ({ds['row_count']} 行)")
    else:
        print(f"✗ 获取失败: {response.status_code}")


def test_get_dataset(dataset_id: int):
    """测试获取单个数据集详情"""
    print(f"\n获取数据集详情 (ID: {dataset_id}):")
    response = requests.get(f"{BASE_URL}/upload/datasets/{dataset_id}")

    if response.status_code == 200:
        dataset = response.json()
        print(f"✓ 数据集名称: {dataset['name']}")
        print(f"  描述: {dataset['description']}")
        print(f"  文件路径: {dataset['file_path']}")
    else:
        print(f"✗ 获取失败: {response.status_code}")


def test_delete_dataset(dataset_id: int):
    """测试删除数据集"""
    print(f"\n删除数据集 (ID: {dataset_id}):")
    response = requests.delete(f"{BASE_URL}/upload/datasets/{dataset_id}")

    if response.status_code == 200:
        print(f"✓ 删除成功: {response.json()['message']}")
    else:
        print(f"✗ 删除失败: {response.status_code}")


def main():
    print("=" * 50)
    print("文件上传功能测试")
    print("=" * 50)

    # 检查服务器是否运行
    try:
        response = requests.get(f"{BASE_URL}/")
        print(f"✓ 服务器正在运行: {response.json()['message']}\n")
    except Exception as e:
        print(f"✗ 无法连接到服务器，请先启动服务器:")
        print("  uvicorn backend.main:app --reload")
        return

    # 创建测试文件
    test_file = create_sample_csv()

    # 测试上传
    dataset_id = test_upload_file(test_file)

    if dataset_id:
        # 测试列表
        test_list_datasets()

        # 测试获取详情
        test_get_dataset(dataset_id)

        # 测试删除
        # test_delete_dataset(dataset_id)

    # 清理测试文件
    if os.path.exists(test_file):
        os.remove(test_file)
        print(f"\n✓ 已清理测试文件: {test_file}")


if __name__ == "__main__":
    main()
