import React, { useState, useEffect } from 'react';
import './ChartConfig.css';

const ChartConfig = ({ dataset, onGenerateChart, loading, chartData }) => {
  const [chartType, setChartType] = useState('bar');
  const [title, setTitle] = useState('');
  const [parameters, setParameters] = useState({});
  const [errors, setErrors] = useState({});

  // 获取数据集的列信息
  const columns = dataset?.schema_json || [];
  const numericColumns = columns.filter(col =>
    col.dtype.includes('BIGINT') ||
    col.dtype.includes('DOUBLE') ||
    col.dtype.includes('FLOAT') ||
    col.dtype.includes('INT')
  );
  const categoricalColumns = columns.filter(col =>
    col.dtype.includes('VARCHAR') ||
    col.dtype.includes('TEXT') ||
    col.dtype.includes('CHAR')
  );
  const dateColumns = columns.filter(col =>
    col.dtype.includes('DATE') ||
    col.dtype.includes('TIME')
  );

  // 图表类型配置
  const chartTypes = [
    { value: 'bar', label: '柱状图', icon: '📊', description: '按类别显示数值对比' },
    { value: 'pie', label: '饼图', icon: '🥧', description: '显示各部分占比' },
    { value: 'timeseries', label: '时间序列', icon: '📈', description: '显示数据随时间变化' },
    { value: 'distribution', label: '分布图', icon: '📉', description: '显示数值分布情况' },
    { value: 'heatmap', label: '热力图', icon: '🔥', description: '显示数值相关性' },
  ];

  // 图表参数配置
  const parameterConfigs = {
    bar: {
      required: ['category_col', 'value_col'],
      optional: ['agg', 'top_k'],
      defaults: {
        agg: 'sum',
        top_k: 8
      }
    },
    pie: {
      required: ['category_col', 'value_col'],
      optional: ['agg', 'top_k'],
      defaults: {
        agg: 'sum',
        top_k: 8
      }
    },
    timeseries: {
      required: ['time_col', 'value_col'],
      optional: ['freq', 'agg', 'group_by', 'time_range'],
      defaults: {
        freq: 'D',
        agg: 'sum'
      }
    },
    distribution: {
      required: ['value_col'],
      optional: ['bins'],
      defaults: {}
    },
    heatmap: {
      required: [],
      optional: ['columns'],
      defaults: {}
    }
  };

  // 聚合方法选项
  const aggregationMethods = [
    { value: 'sum', label: '求和' },
    { value: 'count', label: '计数' },
    { value: 'mean', label: '平均值' },
    { value: 'median', label: '中位数' },
  ];

  // 频率选项
  const frequencyOptions = [
    { value: 'D', label: '天' },
    { value: 'W', label: '周' },
    { value: 'M', label: '月' },
  ];

  // 当图表类型改变时，重置参数
  useEffect(() => {
    const config = parameterConfigs[chartType];
    if (config) {
      setParameters({ ...config.defaults });
      setErrors({});
    }
  }, [chartType]);

  // 生成默认标题
  useEffect(() => {
    const chartTypeConfig = chartTypes.find(t => t.value === chartType);
    if (chartTypeConfig) {
      setTitle(`${chartTypeConfig.label} - ${dataset?.name || '数据可视化'}`);
    }
  }, [chartType, dataset?.name]);

  // 验证参数
  const validateParameters = () => {
    const newErrors = {};
    const config = parameterConfigs[chartType];

    if (config) {
      // 检查必填参数
      config.required.forEach(param => {
        if (!parameters[param]) {
          newErrors[param] = `${param} 是必填参数`;
        }
      });
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // 处理生成图表
  const handleGenerate = () => {
    if (!validateParameters()) {
      return;
    }

    const requestData = {
      chart_type: chartType,
      title: title || undefined,
      ...parameters
    };

    // 移除空值参数
    Object.keys(requestData).forEach(key => {
      if (requestData[key] === undefined || requestData[key] === '' ||
          (Array.isArray(requestData[key]) && requestData[key].length === 0)) {
        delete requestData[key];
      }
    });

    onGenerateChart(requestData);
  };

  // 获取可选的列列表
  const getColumnsForParam = (param) => {
    switch (param) {
      case 'category_col':
        return categoricalColumns;
      case 'value_col':
        return numericColumns;
      case 'time_col':
        return dateColumns;
      case 'group_by':
        return categoricalColumns;
      case 'columns':
        return numericColumns;
      default:
        return columns;
    }
  };

  const config = parameterConfigs[chartType] || {};

  return (
    <div className="chart-config-container">
      <div className="config-header">
        <h3>图表配置</h3>
        <p className="config-description">为数据集 "{dataset?.name}" 创建可视化图表</p>
      </div>

      {/* 图表类型选择 */}
      <div className="config-section">
        <label className="section-label">图表类型</label>
        <div className="chart-types-grid">
          {chartTypes.map(type => (
            <button
              key={type.value}
              className={`chart-type-card ${chartType === type.value ? 'active' : ''}`}
              onClick={() => setChartType(type.value)}
            >
              <div className="chart-type-icon">{type.icon}</div>
              <div className="chart-type-label">{type.label}</div>
              <div className="chart-type-description">{type.description}</div>
            </button>
          ))}
        </div>
      </div>

      {/* 图表标题 */}
      <div className="config-section">
        <label className="field-label">图表标题 (可选)</label>
        <input
          type="text"
          className="field-input"
          placeholder="输入图表标题..."
          value={title}
          onChange={(e) => setTitle(e.target.value)}
        />
      </div>

      {/* 动态参数配置 */}
      <div className="config-section">
        <label className="section-label">图表参数</label>

        {/* 必填参数 */}
        {config.required.map(param => (
          <div key={param} className="field-group">
            <label className="field-label required">
              {param.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
            </label>
            {param.includes('col') || param.includes('columns') ? (
              getColumnsForParam(param).length > 0 ? (
                param === 'columns' ? (
                  <select
                    className="field-input"
                    value={parameters[param] || ''}
                    onChange={(e) => setParameters({ ...parameters, [param]: e.target.value ? [e.target.value] : [] })}
                  >
                    <option value="">选择数值列...</option>
                    {getColumnsForParam(param).map(col => (
                      <option key={col.name} value={col.name}>{col.name}</option>
                    ))}
                  </select>
                ) : (
                  <select
                    className="field-input"
                    value={parameters[param] || ''}
                    onChange={(e) => setParameters({ ...parameters, [param]: e.target.value })}
                  >
                    <option value="">选择列...</option>
                    {getColumnsForParam(param).map(col => (
                      <option key={col.name} value={col.name}>{col.name}</option>
                    ))}
                  </select>
                )
              ) : (
                <input
                  type="text"
                  className="field-input"
                  placeholder={`输入 ${param}...`}
                  value={parameters[param] || ''}
                  onChange={(e) => setParameters({ ...parameters, [param]: e.target.value })}
                />
              )
            ) : (
              <input
                type="text"
                className="field-input"
                placeholder={`输入 ${param}...`}
                value={parameters[param] || ''}
                onChange={(e) => setParameters({ ...parameters, [param]: e.target.value })}
              />
            )}
            {errors[param] && <span className="field-error">{errors[param]}</span>}
          </div>
        ))}

        {/* 可选参数 */}
        {config.optional.map(param => {
          if (param === 'agg') {
            return (
              <div key={param} className="field-group">
                <label className="field-label">聚合方式</label>
                <select
                  className="field-input"
                  value={parameters[param] || config.defaults[param] || 'sum'}
                  onChange={(e) => setParameters({ ...parameters, [param]: e.target.value })}
                >
                  {aggregationMethods.map(method => (
                    <option key={method.value} value={method.value}>{method.label}</option>
                  ))}
                </select>
              </div>
            );
          }

          if (param === 'freq') {
            return (
              <div key={param} className="field-group">
                <label className="field-label">时间频率</label>
                <select
                  className="field-input"
                  value={parameters[param] || config.defaults[param] || 'D'}
                  onChange={(e) => setParameters({ ...parameters, [param]: e.target.value })}
                >
                  {frequencyOptions.map(freq => (
                    <option key={freq.value} value={freq.value}>{freq.label}</option>
                  ))}
                </select>
              </div>
            );
          }

          if (param === 'top_k') {
            return (
              <div key={param} className="field-group">
                <label className="field-label">显示数量 (Top K)</label>
                <input
                  type="number"
                  className="field-input"
                  min="1"
                  max="50"
                  value={parameters[param] || config.defaults[param] || 8}
                  onChange={(e) => setParameters({ ...parameters, [param]: parseInt(e.target.value) })}
                />
              </div>
            );
          }

          if (param === 'bins') {
            return (
              <div key={param} className="field-group">
                <label className="field-label">分组数量 (Bins)</label>
                <input
                  type="number"
                  className="field-input"
                  min="5"
                  max="100"
                  value={parameters[param] || ''}
                  onChange={(e) => setParameters({ ...parameters, [param]: parseInt(e.target.value) || undefined })}
                  placeholder="自动"
                />
              </div>
            );
          }

          if (param.includes('col')) {
            return (
              <div key={param} className="field-group">
                <label className="field-label">
                  {param.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                </label>
                {getColumnsForParam(param).length > 0 ? (
                  <select
                    className="field-input"
                    value={parameters[param] || ''}
                    onChange={(e) => setParameters({ ...parameters, [param]: e.target.value })}
                  >
                    <option value="">选择列...</option>
                    {getColumnsForParam(param).map(col => (
                      <option key={col.name} value={col.name}>{col.name}</option>
                    ))}
                  </select>
                ) : (
                  <input
                    type="text"
                    className="field-input"
                    placeholder={`输入 ${param}...`}
                    value={parameters[param] || ''}
                    onChange={(e) => setParameters({ ...parameters, [param]: e.target.value })}
                  />
                )}
              </div>
            );
          }

          return (
            <div key={param} className="field-group">
              <label className="field-label">
                {param.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
              </label>
              <input
                type="text"
                className="field-input"
                placeholder={`输入 ${param}...`}
                value={parameters[param] || ''}
                onChange={(e) => setParameters({ ...parameters, [param]: e.target.value })}
              />
            </div>
          );
        })}
      </div>

      {/* 生成按钮 */}
      <div className="config-actions">
        <button
          className="generate-btn"
          onClick={handleGenerate}
          disabled={loading || config.required.some(param => !parameters[param])}
        >
          {loading ? '生成中...' : '生成图表'}
        </button>
      </div>
    </div>
  );
};

export default ChartConfig;