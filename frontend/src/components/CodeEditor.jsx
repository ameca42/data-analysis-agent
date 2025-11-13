import React, { useState } from 'react';
import './ThreeColumnLayout.css';

const CodeEditor = () => {
  const [activeAgent, setActiveAgent] = useState('python');
  const [agents, setAgents] = useState([
    {
      id: 'python',
      name: 'Python Agent',
      icon: '🐍',
      color: '#3776ab',
      description: 'Python 数据分析专家'
    },
    {
      id: 'sql',
      name: 'SQL Agent',
      icon: '🗃️',
      color: '#00758f',
      description: 'SQL 数据库查询专家'
    },
    {
      id: 'visualization',
      name: 'Visualization Agent',
      icon: '📊',
      color: '#ff6f61',
      description: '数据可视化专家'
    },
    {
      id: 'ml',
      name: 'ML Agent',
      icon: '🤖',
      color: '#7b68ee',
      description: '机器学习专家'
    }
  ]);

  const [notebooks, setNotebooks] = useState({
    python: [
      {
        id: 1,
        code: "# Python 数据分析示例\nimport pandas as pd\nimport matplotlib.pyplot as plt\nimport seaborn as sns\n\n# 读取数据\ndf = pd.read_csv('data.csv')\n\n# 数据清洗\ndf = df.dropna()\ndf['date'] = pd.to_datetime(df['date'])\n\n# 基本统计\nprint(\"数据基本信息:\")\nprint(df.info())\nprint(\"\\n数据描述:\")\nprint(df.describe())",
        output: "数据基本信息:\n<class 'pandas.core.frame.DataFrame'>\nRangeIndex: 1000 entries, 0 to 999\nData columns (total 5 columns):\ndate    1000 non-null datetime64[ns]\nvalue   1000 non-null float64\ncategory 1000 non-null object\n...",
        isActive: true
      }
    ],
    sql: [
      {
        id: 1,
        code: "-- SQL 数据查询示例\n-- 查看数据表结构\nSELECT * FROM information_schema.columns \nWHERE table_name = 'sales_data';\n\n-- 基本数据查询\nSELECT \n    date,\n    product_category,\n    SUM(revenue) as total_revenue,\n    COUNT(*) as transaction_count\nFROM sales_data \nWHERE date >= '2024-01-01'\nGROUP BY date, product_category\nORDER BY date DESC;",
        output: "date        | product_category | total_revenue | transaction_count\n------------|-----------------|---------------|------------------\n2024-11-13 | Electronics    | 15420.50      | 45\n2024-11-13 | Clothing        | 8930.75       | 32\n2024-11-12 | Electronics    | 12150.00      | 38",
        isActive: true
      }
    ],
    visualization: [
      {
        id: 1,
        code: "# 数据可视化示例\nimport matplotlib.pyplot as plt\nimport seaborn as sns\nimport plotly.express as px\n\n# 设置绘图风格\nplt.style.use('seaborn-v0_8')\nsns.set_palette(\"husl\")\n\n# 创建子图\nfig, axes = plt.subplots(2, 2, figsize=(15, 12))\nfig.suptitle('数据分析可视化', fontsize=16, fontweight='bold')\n\n# 1. 时间序列图\naxes[0, 0].plot(df['date'], df['value'])\naxes[0, 0].set_title('时间序列趋势')\naxes[0, 0].set_xlabel('日期')\naxes[0, 0].set_ylabel('数值')\naxes[0, 0].grid(True, alpha=0.3)",
        output: "📊 图表输出：\n成功生成了 2x2 的子图布局，包含时间序列图、分布图、相关性热图和分类统计图。",
        isActive: true
      }
    ],
    ml: [
      {
        id: 1,
        code: "# 机器学习示例\nfrom sklearn.model_selection import train_test_split\nfrom sklearn.ensemble import RandomForestRegressor\nfrom sklearn.metrics import mean_squared_error, r2_score\nimport numpy as np\n\n# 准备数据\nX = df[['feature1', 'feature2', 'feature3']]\ny = df['target']\n\n# 分割数据集\nX_train, X_test, y_train, y_test = train_test_split(\n    X, y, test_size=0.2, random_state=42\n)\n\n# 训练模型\nmodel = RandomForestRegressor(n_estimators=100, random_state=42)\nmodel.fit(X_train, y_train)",
        output: "模型训练完成！\n\n训练集 R² 分数: 0.8742\n测试集 R² 分数: 0.8231\n均方误差 (MSE): 12.45\n\n特征重要性:\n- feature1: 0.452\n- feature2: 0.321\n- feature3: 0.227",
        isActive: true
      }
    ]
  });

  const currentAgent = agents.find(agent => agent.id === activeAgent);
  const currentNotebooks = notebooks[activeAgent] || [];

  const addNewCell = () => {
    const newCell = {
      id: Date.now(),
      code: `# ${currentAgent.name} 代码单元\n# 在这里输入代码...`,
      output: "等待执行...",
      isActive: true
    };

    setNotebooks(prev => ({
      ...prev,
      [activeAgent]: [...prev[activeAgent], newCell]
    }));
  };

  const deleteCell = (cellId) => {
    setNotebooks(prev => ({
      ...prev,
      [activeAgent]: prev[activeAgent].filter(cell => cell.id !== cellId)
    }));
  };

  return (
    <div className="code-editor">
      {/* Agent 选择标签页 */}
      <div className="agent-tabs-header">
        <div className="agent-tabs">
          {agents.map(agent => (
            <button
              key={agent.id}
              className={`agent-tab ${activeAgent === agent.id ? 'active' : ''}`}
              onClick={() => setActiveAgent(agent.id)}
              style={{
                borderColor: activeAgent === agent.id ? agent.color : 'transparent'
              }}
            >
              <span className="agent-tab-icon">{agent.icon}</span>
              <span className="agent-tab-name">{agent.name}</span>
            </button>
          ))}
        </div>
        <button className="agent-add-btn">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="10"></circle>
            <line x1="12" y1="8" x2="12" y2="16"></line>
            <line x1="8" y1="12" x2="16" y2="12"></line>
          </svg>
        </button>
      </div>

      {/* 当前 Agent 信息 */}
      <div className="agent-info-bar">
        <div className="agent-details">
          <span className="agent-current-icon" style={{ color: currentAgent.color }}>
            {currentAgent.icon}
          </span>
          <div>
            <h3 className="agent-current-name">{currentAgent.name}</h3>
            <p className="agent-current-description">{currentAgent.description}</p>
          </div>
        </div>
        <div className="agent-actions">
          <button className="agent-action-btn">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <polygon points="5 3 19 12 5 21 5 3"></polygon>
            </svg>
            运行全部
          </button>
          <button className="agent-action-btn">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M19 14l-7 7m0 0l-7-7m7 7V3"></path>
            </svg>
            保存
          </button>
        </div>
      </div>

      {/* 代码单元区域 */}
      <div className="editor-content">
        {currentNotebooks.length === 0 ? (
          <div className="empty-notebook">
            <div className="empty-notebook-icon">{currentAgent.icon}</div>
            <h3>开始使用 {currentAgent.name}</h3>
            <p>点击下方按钮添加第一个代码单元</p>
          </div>
        ) : (
          currentNotebooks.map(cell => (
            <div key={cell.id} className="notebook-cell">
              <div className="cell-header">
                <span className="cell-number">[{cell.isActive ? ' ' : '*'}]:</span>
                <div className="cell-actions">
                  <button className="cell-btn run-btn" title="运行">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <polygon points="5 3 19 12 5 21 5 3"></polygon>
                    </svg>
                  </button>
                  <button
                    className="cell-btn delete-btn"
                    title="删除"
                    onClick={() => deleteCell(cell.id)}
                  >
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <polyline points="3,6 5,6 21,6"></polyline>
                      <path d="M19,6v14a2,2,0,0,1-2,2H7a2,2,0,0,1-2-2V6m3,0V4a2,2,0,0,1,2-2h4a2,2,0,0,1,2,2v2"></path>
                    </svg>
                  </button>
                </div>
              </div>
              <div className="cell-input">
                <textarea
                  className="code-input"
                  placeholder="在这里输入代码..."
                  rows={Math.max(4, cell.code.split('\n').length)}
                  defaultValue={cell.code}
                />
              </div>
              {cell.output && (
                <div className="cell-output">
                  <div className="output-header">
                    <span>输出:</span>
                    <div className="output-actions">
                      <button className="output-btn">复制</button>
                      <button className="output-btn">清除</button>
                    </div>
                  </div>
                  <div className="output-content">
                    {cell.output.includes('📊') ? (
                      <div className="output-chart">
                        <div className="chart-placeholder">
                          {cell.output}
                        </div>
                      </div>
                    ) : (
                      <pre>
                        <code>{cell.output}</code>
                      </pre>
                    )}
                  </div>
                </div>
              )}
            </div>
          ))
        )}

        {/* 添加新单元格按钮 */}
        <button className="add-cell-btn" onClick={addNewCell}>
          <span className="add-icon">+</span>
          添加 {currentAgent.name} 代码单元
        </button>
      </div>
    </div>
  );
};

export default CodeEditor;