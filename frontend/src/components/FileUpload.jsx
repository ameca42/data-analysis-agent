import React, { useState } from 'react';
import { uploadFile } from '../api';
import './FileUpload.css';

const FileUpload = ({ onUploadSuccess }) => {
  const [file, setFile] = useState(null);
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState('');
  const [dragActive, setDragActive] = useState(false);

  // 支持的文件类型
  const acceptedTypes = '.csv,.xlsx,.xls,.json,.parquet';

  // 格式化文件大小
  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  };

  // 处理文件选择
  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      setFile(selectedFile);
      if (!name) {
        setName(selectedFile.name.replace(/\.[^/.]+$/, '')); // 去除扩展名
      }
      setError('');
    }
  };

  // 处理拖拽
  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  // 处理文件放置
  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const droppedFile = e.dataTransfer.files[0];
      setFile(droppedFile);
      if (!name) {
        setName(droppedFile.name.replace(/\.[^/.]+$/, ''));
      }
      setError('');
    }
  };

  // 处理上传
  const handleUpload = async (e) => {
    e.preventDefault();

    if (!file) {
      setError('请选择要上传的文件');
      return;
    }

    setUploading(true);
    setError('');
    setProgress(0);

    try {
      const result = await uploadFile(file, name, description, setProgress);
      console.log('上传成功:', result);

      // 重置表单
      setFile(null);
      setName('');
      setDescription('');
      setProgress(0);

      // 通知父组件
      if (onUploadSuccess) {
        onUploadSuccess(result);
      }

      // 显示成功消息
      alert(`文件上传成功！\n数据集: ${result.name}\n行数: ${result.row_count}`);
    } catch (err) {
      console.error('上传失败:', err);
      setError(typeof err === 'string' ? err : '上传失败，请重试');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="file-upload-container">
      <h2>上传数据文件</h2>

      <form onSubmit={handleUpload} className="upload-form">
        {/* 拖拽区域 */}
        <div
          className={`drop-zone ${dragActive ? 'active' : ''} ${file ? 'has-file' : ''}`}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
          onClick={() => document.getElementById('fileInput').click()}
        >
          <input
            id="fileInput"
            type="file"
            accept={acceptedTypes}
            onChange={handleFileChange}
            style={{ display: 'none' }}
          />

          {!file ? (
            <>
              <div className="upload-icon">📁</div>
              <p className="drop-text">拖拽文件到这里，或点击选择文件</p>
              <p className="file-types">支持: CSV, Excel, JSON, Parquet</p>
            </>
          ) : (
            <div className="file-info">
              <div className="file-icon">📄</div>
              <div className="file-details">
                <p className="file-name">{file.name}</p>
                <p className="file-size">{formatFileSize(file.size)}</p>
              </div>
              <button
                type="button"
                className="remove-file"
                onClick={(e) => {
                  e.stopPropagation();
                  setFile(null);
                  setName('');
                }}
              >
                ✕
              </button>
            </div>
          )}
        </div>

        {/* 上传进度 */}
        {uploading && (
          <div className="progress-container">
            <div className="progress-bar">
              <div
                className="progress-fill"
                style={{ width: `${progress}%` }}
              ></div>
            </div>
            <p className="progress-text">{progress}%</p>
          </div>
        )}

        {/* 数据集信息 */}
        <div className="form-group">
          <label htmlFor="name">数据集名称</label>
          <input
            id="name"
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="例如: 销售数据2023"
            disabled={uploading}
          />
        </div>

        <div className="form-group">
          <label htmlFor="description">描述（可选）</label>
          <textarea
            id="description"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="简要描述这个数据集..."
            rows="3"
            disabled={uploading}
          />
        </div>

        {/* 错误提示 */}
        {error && <div className="error-message">❌ {error}</div>}

        {/* 上传按钮 */}
        <button
          type="submit"
          className="upload-button"
          disabled={!file || uploading}
        >
          {uploading ? '上传中...' : '开始上传'}
        </button>
      </form>
    </div>
  );
};

export default FileUpload;
