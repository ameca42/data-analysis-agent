import React from 'react';
import './DatasetDetail.css';

const DatasetDetail = ({ dataset, onClose }) => {
  if (!dataset) return null;

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
      minute: '2-digit',
      second: '2-digit'
    });
  };

  // 获取数据类型的中文名称
  const getTypeName = (dtype) => {
    const typeMap = {
      'int64': '整数',
      'float64': '浮点数',
      'object': '文本',
      'bool': '布尔值',
      'datetime64': '日期时间'
    };
    return typeMap[dtype] || dtype;
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>📊 数据集详情</h2>
          <button className="close-button" onClick={onClose}>
            ✕
          </button>
        </div>

        <div className="modal-body">
          {/* 基本信息 */}
          <section className="detail-section">
            <h3>基本信息</h3>
            <div className="info-grid">
              <div className="info-item">
                <span className="info-label">数据集名称</span>
                <span className="info-value">{dataset.name}</span>
              </div>
              <div className="info-item">
                <span className="info-label">数据集 ID</span>
                <span className="info-value">{dataset.id}</span>
              </div>
              <div className="info-item">
                <span className="info-label">原始文件名</span>
                <span className="info-value">{dataset.original_filename}</span>
              </div>
              <div className="info-item">
                <span className="info-label">文件类型</span>
                <span className="info-value">{dataset.file_type}</span>
              </div>
              <div className="info-item">
                <span className="info-label">文件大小</span>
                <span className="info-value">{formatFileSize(dataset.file_size)}</span>
              </div>
              <div className="info-item">
                <span className="info-label">状态</span>
                <span className={`status-badge ${dataset.status}`}>
                  {dataset.status === 'active' ? '活跃' : '已删除'}
                </span>
              </div>
              <div className="info-item">
                <span className="info-label">创建时间</span>
                <span className="info-value">{formatDate(dataset.created_at)}</span>
              </div>
              <div className="info-item">
                <span className="info-label">文件路径</span>
                <span className="info-value path">{dataset.file_path}</span>
              </div>
            </div>

            {dataset.description && (
              <div className="description-box">
                <strong>描述：</strong>
                <p>{dataset.description}</p>
              </div>
            )}
          </section>

          {/* 数据统计 */}
          <section className="detail-section">
            <h3>数据统计</h3>
            <div className="stats-cards">
              <div className="stats-card">
                <div className="stats-icon">📏</div>
                <div className="stats-info">
                  <div className="stats-value">{dataset.row_count.toLocaleString()}</div>
                  <div className="stats-label">总行数</div>
                </div>
              </div>
              <div className="stats-card">
                <div className="stats-icon">📋</div>
                <div className="stats-info">
                  <div className="stats-value">{dataset.schema_json?.length || 0}</div>
                  <div className="stats-label">总列数</div>
                </div>
              </div>
            </div>
          </section>

          {/* Schema 信息 */}
          {dataset.schema_json && dataset.schema_json.length > 0 && (
            <section className="detail-section">
              <h3>列信息（Schema）</h3>
              <div className="schema-table-wrapper">
                <table className="schema-table">
                  <thead>
                    <tr>
                      <th>列名</th>
                      <th>数据类型</th>
                      <th>非空</th>
                      <th>空值</th>
                      <th>唯一值</th>
                      <th>统计信息</th>
                    </tr>
                  </thead>
                  <tbody>
                    {dataset.schema_json.map((col, index) => (
                      <tr key={index}>
                        <td className="col-name">{col.name}</td>
                        <td>
                          <span className="type-badge">{getTypeName(col.dtype)}</span>
                        </td>
                        <td>{col.non_null_count.toLocaleString()}</td>
                        <td className={col.null_count > 0 ? 'has-nulls' : ''}>
                          {col.null_count.toLocaleString()}
                        </td>
                        <td>{col.unique_count.toLocaleString()}</td>
                        <td>
                          {col.min !== undefined && (
                            <div className="stats-details">
                              <span>最小: {col.min}</span>
                              <span>最大: {col.max}</span>
                              <span>平均: {col.mean?.toFixed(2)}</span>
                            </div>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
          )}
        </div>

        <div className="modal-footer">
          <button className="close-modal-button" onClick={onClose}>
            关闭
          </button>
        </div>
      </div>
    </div>
  );
};

export default DatasetDetail;
