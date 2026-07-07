# Nexus 3D AI Studio (2Dto3D)

![Nexus 3D](https://img.shields.io/badge/Status-Active-success) ![React](https://img.shields.io/badge/Frontend-React_Three_Fiber-blue) ![Python](https://img.shields.io/badge/Backend-Python_WebSocket-green)

Nexus 3D AI Studio 是一款集成了**从 2D 到 3D 转换**、**3D 场景可视化**以及**AI 自然语言空间控制**于一体的综合性创意平台。本项目最初是一个极简的 `2Dto3D` 转换 MVP 骨架，现已全面进化为一个全栈的 3D 数字人互动工作流。

---

## 🌟 核心功能 (Core Features)

### 1. AI 驱动的 3D 空间交互 (AI-Driven 3D Spatial Interaction)
- **智能坐标解析**：底层接入了大语言模型（如 DeepSeek），使 AI 具备严格的 3D Web 空间坐标系意识（X/Y/Z）。
- **一句话让数字人动起来**：通过文本或语音，你可以对数字人下达诸如*“向左走两步”*、*“转一圈然后挥手”*等自然语言指令。AI 会将这些指令实时转换为动态的三维物理坐标和触发动画。
- **动态语音生成**：数字人在执行动作的同时，还会通过集成的阿里云 DashScope TTS 语音合成技术向你开口说话。

### 2. 沉浸式 3D 引擎面板 (Web3D Canvas)
- **React Three Fiber (R3F)**：采用强大的 R3F 引擎在网页端渲染真实的 3D 物理场景。
- **环境可视化**：支持加载多种 3D 模型格式（GLB、OBJ、3MF 等）。
- **多对象管理面板**：你可以自由切换控制“场景（Scene）”或单独控制“数字人（Avatar）”，提供高精度的六轴手动平移/旋转支持。

### 3. 2Dto3D 骨架流水线 (2D to 3D MVP Pipeline)
保留了项目最初的核心能力骨架，便于未来接入生成式模型：
- FastAPI 后端以及本地作业队列
- 支持图片、SVG、PDF 等输入归一化
- 为 SF3D, TripoSR 等高级图生 3D 模型预留了无缝替换接口

---

## 🚀 快速开始 (Quick Start)

要体验“一句话控制 3D 数字人”的魔法，请分别启动前端和后端：

### 1. 启动前端界面 (Frontend - React Three Fiber)
打开一个命令行终端：
```powershell
cd Nexus-3D-AI-Agent-master\Nexus-3D-AI-Agent-master\frontend2
npm install
npm run dev
```
然后浏览器访问 `http://localhost:5173`。

### 2. 启动智能控制后台 (Backend - Python WebSocket Server)
打开另一个命令行终端：
```powershell
cd Nexus-3D-AI-Agent-master\Nexus-3D-AI-Agent-master\backend2
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python interactive_server.py
```
*(注意：需要配置相应的 API Key 环境变量才能使用大模型自然语言处理和 TTS 语音合成功能。)*

---

## 📦 ArkClaw Skill 技能包 (Extensibility)

本项目不仅提供了完整的交互界面，还将核心的 **3D 空间理解与数字人控制逻辑** 提炼成了独立的 `nexus_3d_controller` 技能包。

- **兼容性**：支持被加载到任何兼容 ArkClaw / OpenClaw 框架的智能体（Agent）中。
- **位置**：此技能包位于 `C:\Users\Asus\Desktop\skills\nexus_3d_controller`，其中包含了标准的 `SKILL.md` 指南与无缝对接前端的执行脚本。
- **赋能**：任何加载了此技能的 Agent，都能瞬间“觉醒”并拥有理解并在 3D 三维坐标系中生成指令的能力。

---

## 🏗️ 架构历史 (Architecture Notes)

- 本仓库的前身是 `HY-1337` 的 2Dto3D 项目。
- 目前的 `local` 生成器仅作为占位符网格后端。一旦模型依赖项准备就绪，可以在 `backend/app/core/generator.py` 中接入高级的图像到 3D 后端引擎。
