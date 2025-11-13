import React from 'react';
import '../styles/appstore.css';

const ThreeColumnLayout = ({
  leftPanel,
  middlePanel,
  rightPanel
}) => {
  return (
    <div className="three-column-layout">
      {/* 左侧面板 - 对话区域 */}
      <aside className="column left-panel">
        <div className="panel-content">
          {leftPanel || (
            <div className="empty-state">
              <div className="empty-state-icon">💬</div>
              <p className="empty-state-title">AI 对话界面</p>
              <p className="empty-state-description">
                与 AI 助手进行数据分析对话
              </p>
            </div>
          )}
        </div>
      </aside>

      {/* 中间面板 - 代码编辑区域 */}
      <main className="column middle-panel">
        <div className="panel-content">
          {middlePanel || (
            <div className="empty-state">
              <div className="empty-state-icon">📝</div>
              <p className="empty-state-title">Jupyter 风格代码编辑器</p>
              <p className="empty-state-description">
                编写和执行数据分析代码
              </p>
            </div>
          )}
        </div>
      </main>

      {/* 右侧面板 - 数据集和可视化区域 */}
      <aside className="column right-panel">
        <div className="panel-content">
          {rightPanel || (
            <div className="empty-state">
              <div className="empty-state-icon">📊</div>
              <p className="empty-state-title">数据管理</p>
              <p className="empty-state-description">
                管理数据集和查看可视化结果
              </p>
            </div>
          )}
        </div>
      </aside>
    </div>
  );
};

export default ThreeColumnLayout;