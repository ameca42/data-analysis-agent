import { useState } from 'react';
import FileUpload from './components/FileUpload';
import DatasetList from './components/DatasetList';
import './App.css';

function App() {
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  // 上传成功后刷新列表
  const handleUploadSuccess = () => {
    setRefreshTrigger(prev => prev + 1);
  };

  return (
    <div className="app">
      <header className="app-header">
        <div className="app-header-content">
          <h1>数据分析 Agent</h1>
          <p className="app-subtitle">智能数据分析与可视化平台</p>
        </div>
      </header>

      <main className="app-main">
        <FileUpload onUploadSuccess={handleUploadSuccess} />
        <DatasetList refreshTrigger={refreshTrigger} />
      </main>

      <footer className="app-footer">
        <p>© 2024 数据分析 Agent | Powered by FastAPI & React</p>
      </footer>
    </div>
  );
}

export default App;
