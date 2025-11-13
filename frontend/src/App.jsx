import React from 'react';
import ThreeColumnLayout from './components/ThreeColumnLayout';
import ChatPanel from './components/ChatPanel';
import CodeEditor from './components/CodeEditor';
import DataPanel from './components/DataPanel';
import './styles/appstore.css';
import './App-new.css';

function App() {
  return (
    <div className="app-new">
      <ThreeColumnLayout
        leftPanel={<ChatPanel />}
        middlePanel={<CodeEditor />}
        rightPanel={<DataPanel />}
      />
    </div>
  );
}

export default App;
