import React, { useEffect, useRef } from 'react';
import Plot from 'react-plotly.js';
import './ChartView.css';

const ChartView = ({ chartData, loading, error, onRetry }) => {
  const plotRef = useRef(null);

  // 如果正在加载
  if (loading) {
    return (
      <div className="chart-view-container">
        <div className="chart-loading">
          <div className="loading-spinner"></div>
          <p>正在生成图表...</p>
        </div>
      </div>
    );
  }

  // 如果有错误
  if (error) {
    return (
      <div className="chart-view-container">
        <div className="chart-error">
          <div className="error-icon">⚠️</div>
          <h3>图表生成失败</h3>
          <p>{error}</p>
          {onRetry && (
            <button className="retry-btn" onClick={onRetry}>
              重试
            </button>
          )}
        </div>
      </div>
    );
  }

  // 如果没有图表数据
  if (!chartData || !chartData.data || !chartData.layout) {
    return (
      <div className="chart-view-container">
        <div className="chart-empty">
          <div className="empty-icon">📊</div>
          <p>请配置图表参数以生成可视化图表</p>
        </div>
      </div>
    );
  }

  // 计算图表配置
  const plotConfig = {
    responsive: true,
    displayModeBar: true,
    displaylogo: false,
    modeBarButtonsToRemove: ['pan2d', 'lasso2d', 'select2d'],
    toImageButtonOptions: {
      format: 'png',
      filename: `chart_${Date.now()}`,
      height: 600,
      width: 800,
      scale: 2,
    },
  };

  // 计算布局
  const layout = {
    ...chartData.layout,
    autosize: true,
    paper_bgcolor: 'rgba(0,0,0,0)',
    plot_bgcolor: 'rgba(0,0,0,0)',
    margin: {
      l: 50,
      r: 50,
      t: 80,
      b: 50,
      pad: 4,
    },
    font: {
      family: 'system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
    },
  };

  return (
    <div className="chart-view-container">
      <div className="chart-header">
        <h3 className="chart-title">{chartData.layout.title || '数据可视化图表'}</h3>
        <div className="chart-info">
          {chartData.meta && (
            <div className="chart-meta">
              {chartData.meta.category_col && (
                <span className="meta-item">
                  分类列: <strong>{chartData.meta.category_col}</strong>
                </span>
              )}
              {chartData.meta.value_col && (
                <span className="meta-item">
                  数值列: <strong>{chartData.meta.value_col}</strong>
                </span>
              )}
              {chartData.meta.aggregation && (
                <span className="meta-item">
                  聚合方式: <strong>{chartData.meta.aggregation}</strong>
                </span>
              )}
              {chartData.meta.time_col && (
                <span className="meta-item">
                  时间列: <strong>{chartData.meta.time_col}</strong>
                </span>
              )}
            </div>
          )}
        </div>
      </div>

      <div className="chart-wrapper" ref={plotRef}>
        <Plot
          data={chartData.data}
          layout={layout}
          config={plotConfig}
          style={{ width: '100%', height: '500px' }}
          useResizeHandler={true}
        />
      </div>

      {chartData.summary && (
        <div className="chart-summary">
          <h4>📈 图表摘要</h4>
          <div className="summary-grid">
            {Object.entries(chartData.summary).map(([key, value]) => (
              <div key={key} className="summary-item">
                <span className="summary-label">
                  {key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}:
                </span>
                <span className="summary-value">
                  {typeof value === 'number' ? (
                    value.toLocaleString(undefined, { maximumFractionDigits: 2 })
                  ) : (
                    value
                  )}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default ChartView;