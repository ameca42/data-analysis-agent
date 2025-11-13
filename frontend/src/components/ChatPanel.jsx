import React, { useState } from 'react';
import './ThreeColumnLayout.css';

const ChatPanel = () => {
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');

  const handleSend = () => {
    if (inputValue.trim()) {
      // 简单的消息处理，后续可以连接到实际的聊天 API
      const newMessage = {
        id: Date.now(),
        text: inputValue,
        sender: 'user',
        timestamp: new Date()
      };
      setMessages([...messages, newMessage]);
      setInputValue('');

      // 模拟 AI 回复
      setTimeout(() => {
        const aiReply = {
          id: Date.now() + 1,
          text: '我是您的数据分析助手，请问您需要什么帮助？',
          sender: 'ai',
          timestamp: new Date()
        };
        setMessages(prev => [...prev, aiReply]);
      }, 1000);
    }
  };

  return (
    <div className="chat-panel">
      {/* 消息列表 */}
      <div className="chat-messages">
        {messages.length === 0 ? (
          <div className="chat-empty">
            <div className="chat-empty-icon">🤖</div>
            <p className="chat-empty-title">开始对话</p>
            <p className="chat-empty-description">
              向 AI 助手询问关于数据分析的问题
            </p>
          </div>
        ) : (
          messages.map(message => (
            <div key={message.id} className={`chat-message ${message.sender}`}>
              <div className="message-content">
                {message.text}
              </div>
              <div className="message-time">
                {message.timestamp.toLocaleTimeString()}
              </div>
            </div>
          ))
        )}
      </div>

      {/* 输入区域 */}
      <div className="chat-input-container">
        <div className="chat-input-wrapper">
          <input
            type="text"
            className="chat-input"
            placeholder="输入您的问题..."
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSend()}
          />
          <button
            className="chat-send-btn"
            onClick={handleSend}
            disabled={!inputValue.trim()}
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z"/>
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
};

export default ChatPanel;