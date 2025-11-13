import axios from 'axios';

// 使用相对路径，通过 Vite 代理转发到后端
const API_BASE_URL = '';

/**
 * 上传文件到服务器
 * @param {File} file - 要上传的文件
 * @param {string} name - 数据集名称
 * @param {string} description - 数据集描述
 * @param {function} onProgress - 上传进度回调
 * @returns {Promise} 上传结果
 */
export const uploadFile = async (file, name, description, onProgress) => {
  const formData = new FormData();
  formData.append('file', file);
  if (name) formData.append('name', name);
  if (description) formData.append('description', description);

  try {
    const response = await axios.post(`${API_BASE_URL}/upload/`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (onProgress) {
          const percentCompleted = Math.round(
            (progressEvent.loaded * 100) / progressEvent.total
          );
          onProgress(percentCompleted);
        }
      },
    });
    return response.data;
  } catch (error) {
    throw error.response?.data?.detail || '上传失败';
  }
};

/**
 * 获取数据集列表
 * @param {number} skip - 跳过的记录数
 * @param {number} limit - 返回的最大记录数
 * @returns {Promise} 数据集列表
 */
export const getDatasets = async (skip = 0, limit = 100) => {
  try {
    const response = await axios.get(`${API_BASE_URL}/upload/datasets`, {
      params: { skip, limit },
    });
    return response.data;
  } catch (error) {
    throw error.response?.data?.detail || '获取数据集列表失败';
  }
};

/**
 * 获取单个数据集详情
 * @param {number} datasetId - 数据集ID
 * @returns {Promise} 数据集详情
 */
export const getDataset = async (datasetId) => {
  try {
    const response = await axios.get(`${API_BASE_URL}/upload/datasets/${datasetId}`);
    return response.data;
  } catch (error) {
    throw error.response?.data?.detail || '获取数据集详情失败';
  }
};

/**
 * 删除数据集
 * @param {number} datasetId - 数据集ID
 * @returns {Promise} 删除结果
 */
export const deleteDataset = async (datasetId) => {
  try {
    const response = await axios.delete(`${API_BASE_URL}/upload/datasets/${datasetId}`);
    return response.data;
  } catch (error) {
    throw error.response?.data?.detail || '删除数据集失败';
  }
};

/**
 * 生成图表
 * @param {number} datasetId - 数据集ID
 * @param {Object} chartConfig - 图表配置
 * @returns {Promise} 图表数据
 */
export const generateChart = async (datasetId, chartConfig) => {
  try {
    const response = await axios.post(`${API_BASE_URL}/datasets/${datasetId}/charts`, chartConfig);
    return response.data;
  } catch (error) {
    throw error.response?.data?.detail || '生成图表失败';
  }
};

/**
 * 获取数据集的图表列表
 * @param {number} datasetId - 数据集ID
 * @param {string} chartType - 图表类型（可选）
 * @param {number} limit - 限制数量
 * @returns {Promise} 图表列表
 */
export const getDatasetCharts = async (datasetId, chartType = null, limit = 20) => {
  try {
    const params = { limit };
    if (chartType) params.chart_type = chartType;

    const response = await axios.get(`${API_BASE_URL}/datasets/${datasetId}/charts`, { params });
    return response.data;
  } catch (error) {
    throw error.response?.data?.detail || '获取图表列表失败';
  }
};

/**
 * 获取单个图表数据
 * @param {number} datasetId - 数据集ID
 * @param {number} analysisId - 图表分析ID
 * @returns {Promise} 图表数据
 */
export const getChart = async (datasetId, analysisId) => {
  try {
    const response = await axios.get(`${API_BASE_URL}/datasets/${datasetId}/charts/${analysisId}`);
    return response.data;
  } catch (error) {
    throw error.response?.data?.detail || '获取图表数据失败';
  }
};

/**
 * 删除图表
 * @param {number} datasetId - 数据集ID
 * @param {number} analysisId - 图表分析ID
 * @returns {Promise} 删除结果
 */
export const deleteChart = async (datasetId, analysisId) => {
  try {
    const response = await axios.delete(`${API_BASE_URL}/datasets/${datasetId}/charts/${analysisId}`);
    return response.data;
  } catch (error) {
    throw error.response?.data?.detail || '删除图表失败';
  }
};
