import React, { useState } from 'react';
import FileUpload from './FileUpload';
import DatasetList from './DatasetList';
import ChartManager from './ChartManager';
import './ThreeColumnLayout.css';

const DataPanel = () => {
  const [refreshTrigger, setRefreshTrigger] = useState(0);
  const [showDatasetModal, setShowDatasetModal] = useState(false);

  const handleUploadSuccess = () => {
    setRefreshTrigger(prev => prev + 1);
  };

  return (
    <div className="data-panel">
      {/* 标题栏，包含数据集按钮 */}
      <div className="data-header">
        <h3 className="data-title">数据可视化</h3>
        <button
          className="dataset-toggle-btn"
          onClick={() => setShowDatasetModal(true)}
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path>
            <polyline points="9,22 9,12 15,12 15,22"></polyline>
          </svg>
          数据集管理
        </button>
      </div>

      {/* 内容区域 - 只显示可视化 */}
      <div className="data-content">
        <div className="charts-view">
          <ChartManager />
        </div>
      </div>

      {/* 数据集管理弹窗 */}
      {showDatasetModal && (
        <div className="dataset-modal-overlay" onClick={() => setShowDatasetModal(false)}>
          <div className="dataset-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3 className="modal-title">数据集管理</h3>
              <button
                className="modal-close-btn"
                onClick={() => setShowDatasetModal(false)}
              >
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <line x1="18" y1="6" x2="6" y2="18"></line>
                  <line x1="6" y1="6" x2="18" y2="18"></line>
                </svg>
              </button>
            </div>

            <div className="modal-content">
              <div className="upload-section">
                <FileUpload onUploadSuccess={handleUploadSuccess} />
              </div>
              <div className="datasets-section">
                <DatasetList refreshTrigger={refreshTrigger} />
              </div>

              {/* 添加一些占位内容确保有滚动 */}
              <div style={{
                marginTop: 'var(--spacing-lg)',
                padding: 'var(--spacing-md)',
                background: 'var(--systemQuinary)',
                borderRadius: 'var(--radius-lg)',
                color: 'var(--systemSecondary)',
                fontSize: 'var(--font-size-sm)'
              }}>
                <p style={{ margin: 0 }}>提示：上传的数据集可以在左侧对话框中进行查询和分析</p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default DataPanel;