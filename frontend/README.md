# 数据分析 Agent - React 前端

这是一个现代化的数据分析平台前端应用，使用 React + Vite 构建。

## 功能特性

✨ **文件上传**
- 支持拖拽上传
- 实时上传进度
- 文件类型验证
- 自动文件信息提取

📊 **数据集管理**
- 数据集列表展示
- 详细信息查看
- 删除操作
- 实时刷新

🎨 **现代 UI**
- 响应式设计
- 渐变色主题
- 流畅动画
- 直观交互

## 项目结构

```
frontend/
├── src/
│   ├── components/
│   │   ├── FileUpload.jsx       # 文件上传组件
│   │   ├── FileUpload.css       # 上传组件样式
│   │   ├── DatasetList.jsx      # 数据集列表组件
│   │   ├── DatasetList.css      # 列表组件样式
│   │   ├── DatasetDetail.jsx    # 数据集详情模态框
│   │   └── DatasetDetail.css    # 详情组件样式
│   ├── App.jsx                  # 主应用组件
│   ├── App.css                  # 应用样式
│   ├── api.js                   # API 服务层
│   ├── main.jsx                 # 应用入口
│   └── index.css                # 全局样式
├── index.html                   # HTML 模板
├── vite.config.js              # Vite 配置
└── package.json                # 项目配置

```

## 快速开始

### 1. 安装依赖

```bash
cd frontend
npm install
```

### 2. 启动开发服务器

```bash
npm run dev
```

访问: http://localhost:3000

### 3. 构建生产版本

```bash
npm run build
```

## 组件说明

### FileUpload 组件

**功能：**
- 拖拽上传文件
- 点击选择文件
- 实时上传进度条
- 文件信息预览
- 表单验证

**使用：**
```jsx
<FileUpload onUploadSuccess={handleSuccess} />
```

### DatasetList 组件

**功能：**
- 网格布局展示数据集
- 显示统计信息（行数、列数、大小）
- 查看详情
- 删除操作
- 空状态提示

**使用：**
```jsx
<DatasetList refreshTrigger={trigger} />
```

### DatasetDetail 组件

**功能：**
- 模态框展示详情
- 基本信息展示
- Schema 表格
- 统计信息卡片

**使用：**
```jsx
<DatasetDetail dataset={data} onClose={handleClose} />
```

## API 配置

API 基础 URL 在 `src/api.js` 中配置：

```javascript
const API_BASE_URL = 'http://localhost:8000';
```

开发环境下，Vite 会自动代理 `/upload` 路径到后端服务器（配置在 `vite.config.js`）。

## 技术栈

- **React 18** - UI 框架
- **Vite** - 构建工具
- **Axios** - HTTP 客户端
- **CSS3** - 样式（渐变、动画、Grid、Flexbox）

## 设计亮点

### 1. 渐变色主题
- 紫色系渐变背景
- 统一的视觉风格
- 柔和的色彩过渡

### 2. 拖拽上传
- 视觉反馈（高亮边框）
- 拖拽状态提示
- 支持点击和拖拽两种方式

### 3. 实时反馈
- 上传进度条
- 加载状态
- 错误提示
- 成功消息

### 4. 响应式设计
- 移动端友好
- 自适应布局
- 触摸优化

## 开发提示

### 添加新功能

1. 在 `src/api.js` 添加 API 函数
2. 创建新组件在 `src/components/`
3. 在 `App.jsx` 中引入和使用

### 调试

打开浏览器控制台查看：
- API 请求日志
- 错误信息
- 上传进度

### 自定义样式

主题色定义在各个 CSS 文件中，主要使用：
- 主色: `#667eea` → `#764ba2` (渐变)
- 背景: `#f7fafc`
- 文字: `#2d3748`
- 边框: `#e2e8f0`

## 常见问题

### 1. 端口冲突

修改 `vite.config.js` 中的端口：
```javascript
server: {
  port: 3001, // 改成其他端口
}
```

### 2. CORS 错误

确保后端已配置 CORS：
```python
# backend/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 3. API 连接失败

检查：
- 后端服务是否启动（http://localhost:8000）
- API URL 是否正确
- 网络请求是否被拦截

## 浏览器支持

- Chrome (推荐)
- Firefox
- Safari
- Edge

## 未来优化

- [ ] 添加 TypeScript 支持
- [ ] 集成状态管理（Redux/Zustand）
- [ ] 添加单元测试
- [ ] 添加数据可视化图表
- [ ] 支持暗色模式
- [ ] 添加国际化（i18n）

## 贡献

欢迎提交 Issue 和 Pull Request！

## 许可证

MIT
