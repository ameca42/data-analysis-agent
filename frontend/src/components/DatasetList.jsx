import React, { useState, useEffect } from 'react';
import { getDatasets, deleteDataset } from '../api';
import DatasetDetail from './DatasetDetail';
import './DatasetList.css';

const DatasetList = ({ refreshTrigger }) => {
  const [datasets, setDatasets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedDataset, setSelectedDataset] = useState(null);

  // 加载数据集列表
  const loadDatasets = async () => {
    setLoading(true);
    setError('');
    try {
      const data = await getDatasets();
      setDatasets(data);
    } catch (err) {
      console.error('加载失败:', err);
      setError(typeof err === 'string' ? err : '加载数据集列表失败');
    } finally {
      setLoading(false);
    }
  };

  // 初始加载和刷新时重新加载
  useEffect(() => {
    loadDatasets();
  }, [refreshTrigger]);

  // 格式化文件大小
  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  };

  // 格式化日期
  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  // 获取文件类型图标
  const getFileIcon = (fileType) => {
    const icons = {
      '.csv': 'CSV',
      '.xlsx': 'XLSX',
      '.xls': 'XLS',
      '.json': 'JSON',
      '.parquet': 'PARQUET'
    };
    return icons[fileType] || 'FILE';
  };

  // 删除数据集
  const handleDelete = async (datasetId, datasetName) => {
    if (!window.confirm(`确定要删除数据集 "${datasetName}" 吗？`)) {
      return;
    }

    try {
      await deleteDataset(datasetId);
      // 重新加载列表
      loadDatasets();
      // 如果当前查看的就是被删除的数据集，关闭详情
      if (selectedDataset?.id === datasetId) {
        setSelectedDataset(null);
      }
    } catch (err) {
      alert(`删除失败: ${err}`);
    }
  };

  if (loading) {
    return (
      <div className="dataset-list-container">
        <h2>数据集列表</h2>
        <div className="loading">加载中...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="dataset-list-container">
        <h2>数据集列表</h2>
        <div className="error-message">{error}</div>
        <button onClick={loadDatasets} className="retry-button">
          重试
        </button>
      </div>
    );
  }

  return (
    <div className="dataset-list-container">
      <div className="list-header">
        <h2>数据集列表</h2>
        <button onClick={loadDatasets} className="refresh-button">
          刷新
        </button>
      </div>

      {datasets.length === 0 ? (
        <div className="empty-state">
          <p className="empty-icon">Empty</p>
          <p className="empty-text">还没有上传任何数据集</p>
          <p className="empty-hint">上传第一个文件开始数据分析吧！</p>
        </div>
      ) : (
        <div className="datasets-grid">
          {datasets.map((dataset) => (
            <div key={dataset.id} className="dataset-card">
              <div className="card-header">
                <span className="file-type-icon">
                  {getFileIcon(dataset.file_type)}
                </span>
                <div className="card-title">
                  <h3>{dataset.name}</h3>
                  <span className="dataset-id">ID: {dataset.id}</span>
                </div>
              </div>

              {dataset.description && (
                <p className="dataset-description">{dataset.description}</p>
              )}

              <div className="dataset-stats">
                <div className="stat">
                  <span className="stat-label">行数</span>
                  <span className="stat-value">{dataset.row_count.toLocaleString()}</span>
                </div>
                <div className="stat">
                  <span className="stat-label">列数</span>
                  <span className="stat-value">{dataset.schema_json?.length || 0}</span>
                </div>
                <div className="stat">
                  <span className="stat-label">大小</span>
                  <span className="stat-value">{formatFileSize(dataset.file_size)}</span>
                </div>
              </div>

              <div className="dataset-meta">
                <span className="file-name" title={dataset.original_filename}>
                  File: {dataset.original_filename}
                </span>
                <span className="created-date">
                  Created: {formatDate(dataset.created_at)}
                </span>
              </div>

              <div className="card-actions">
                <button
                  className="btn-view"
                  onClick={() => setSelectedDataset(dataset)}
                >
                  查看详情
                </button>
                <button
                  className="btn-delete"
                  onClick={() => handleDelete(dataset.id, dataset.name)}
                >
                  删除
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* 数据集详情模态框 */}
      {selectedDataset && (
        <DatasetDetail
          dataset={selectedDataset}
          onClose={() => setSelectedDataset(null)}
        />
      )}
    </div>
  );
};

export default DatasetList;
