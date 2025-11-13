import React, { useState, useEffect } from 'react';
import ChartConfig from './ChartConfig';
import ChartView from './ChartView';
import { generateChart, getDatasetCharts, deleteChart } from '../api';
import './ChartManager.css';

const ChartManager = ({ dataset }) => {
  const [chartData, setChartData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [savedCharts, setSavedCharts] = useState([]);
  const [loadingCharts, setLoadingCharts] = useState(false);
  const [activeTab, setActiveTab] = useState('create'); // 'create' | 'gallery'

  // 加载已保存的图表
  const loadSavedCharts = async () => {
    if (!dataset?.id) return;

    setLoadingCharts(true);
    try {
      const charts = await getDatasetCharts(dataset.id);
      setSavedCharts(charts.charts || []);
    } catch (err) {
      console.error('加载图表列表失败:', err);
    } finally {
      setLoadingCharts(false);
    }
  };

  useEffect(() => {
    if (activeTab === 'gallery') {
      loadSavedCharts();
    }
  }, [activeTab, dataset?.id]);

  // 生成图表
  const handleGenerateChart = async (config) => {
    setLoading(true);
    setError('');
    setChartData(null);

    try {
      const result = await generateChart(dataset.id, config);
      setChartData(result);

      // 生成成功后，刷新图表列表
      if (activeTab === 'gallery') {
        loadSavedCharts();
      }
    } catch (err) {
      setError(typeof err === 'string' ? err : '生成图表失败');
    } finally {
      setLoading(false);
    }
  };

  // 加载已保存的图表
  const handleLoadChart = async (chartId) => {
    setLoading(true);
    setError('');

    try {
      const chart = await getChart(dataset.id, chartId);
      setChartData(chart);
      setActiveTab('create'); // 切换到创建标签查看图表
    } catch (err) {
      setError(typeof err === 'string' ? err : '加载图表失败');
    } finally {
      setLoading(false);
    }
  };

  // 删除已保存的图表
  const handleDeleteChart = async (chartId, chartTitle) => {
    if (!window.confirm(`确定要删除图表 "${chartTitle}" 吗？`)) {
      return;
    }

    try {
      await deleteChart(dataset.id, chartId);
      // 刷新图表列表
      loadSavedCharts();

      // 如果当前显示的是被删除的图表，清除显示
      if (chartData && chartData.chart_id === chartId) {
        setChartData(null);
      }
    } catch (err) {
      alert(`删除图表失败: ${err}`);
    }
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

  // 获取图表类型图标
  const getChartTypeIcon = (chartType) => {
    const icons = {
      'bar': '📊',
      'pie': '🥧',
      'timeseries': '📈',
      'distribution': '📉',
      'heatmap': '🔥'
    };
    return icons[chartType] || '📊';
  };

  // 获取图表类型名称
  const getChartTypeName = (chartType) => {
    const names = {
      'bar': '柱状图',
      'pie': '饼图',
      'timeseries': '时间序列',
      'distribution': '分布图',
      'heatmap': '热力图'
    };
    return names[chartType] || chartType;
  };

  return (
    <div className="chart-manager">
      <div className="chart-manager-header">
        <h2>📊 图表分析</h2>
        <p>为数据集 "{dataset?.name}" 创建和管理可视化图表</p>
      </div>

      {/* 标签页 */}
      <div className="chart-tabs">
        <button
          className={`tab-button ${activeTab === 'create' ? 'active' : ''}`}
          onClick={() => setActiveTab('create')}
        >
          创建图表
        </button>
        <button
          className={`tab-button ${activeTab === 'gallery' ? 'active' : ''}`}
          onClick={() => setActiveTab('gallery')}
        >
          图表库 {savedCharts.length > 0 && `(${savedCharts.length})`}
        </button>
      </div>

      {/* 内容区域 */}
      <div className="chart-content">
        {activeTab === 'create' && (
          <div className="create-chart-view">
            <ChartConfig
              dataset={dataset}
              onGenerateChart={handleGenerateChart}
              loading={loading}
              chartData={chartData}
            />

            {/* 图表显示区域 */}
            {chartData && (
              <div className="chart-result-section">
                <ChartView
                  chartData={chartData}
                  loading={loading}
                  error={error}
                  onRetry={() => handleGenerateChart({})}
                />
              </div>
            )}
          </div>
        )}

        {activeTab === 'gallery' && (
          <div className="chart-gallery-view">
            {loadingCharts ? (
              <div className="gallery-loading">
                <div className="loading-spinner"></div>
                <p>加载图表库中...</p>
              </div>
            ) : savedCharts.length === 0 ? (
              <div className="gallery-empty">
                <div className="empty-icon">📊</div>
                <h3>还没有保存的图表</h3>
                <p>创建你的第一个图表开始数据分析吧！</p>
                <button
                  className="create-first-btn"
                  onClick={() => setActiveTab('create')}
                >
                  创建第一个图表
                </button>
              </div>
            ) : (
              <div className="charts-grid">
                {savedCharts.map((chart) => (
                  <div key={chart.id} className="chart-card">
                    <div className="chart-card-header">
                      <span className="chart-icon">
                        {getChartTypeIcon(chart.chart_type)}
                      </span>
                      <div className="chart-info">
                        <h4 className="chart-title">{chart.title}</h4>
                        <p className="chart-type">
                          {getChartTypeName(chart.chart_type)}
                        </p>
                      </div>
                    </div>

                    <div className="chart-meta-info">
                      <div className="meta-item">
                        <span className="meta-label">创建时间:</span>
                        <span className="meta-value">{formatDate(chart.created_at)}</span>
                      </div>
                      <div className="meta-item">
                        <span className="meta-label">执行时间:</span>
                        <span className="meta-value">{chart.execution_time?.toFixed(2)}s</span>
                      </div>
                      {chart.summary && Object.keys(chart.summary).length > 0 && (
                        <div className="chart-summary-mini">
                          {Object.entries(chart.summary).slice(0, 2).map(([key, value]) => (
                            <div key={key} className="summary-item">
                              <span className="summary-label">
                                {key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}:
                              </span>
                              <span className="summary-value">
                                {typeof value === 'number' ?
                                  value.toLocaleString(undefined, { maximumFractionDigits: 1 }) :
                                  value
                                }
                              </span>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>

                    <div className="chart-actions">
                      <button
                        className="view-btn"
                        onClick={() => handleLoadChart(chart.id)}
                      >
                        查看
                      </button>
                      <button
                        className="delete-btn"
                        onClick={() => handleDeleteChart(chart.id, chart.title)}
                      >
                        删除
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default ChartManager;