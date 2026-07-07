# 点豆成金 (bean-to-gold) 🎨

[![Spring Boot](https://img.shields.io/badge/Backend-Spring%20Boot%203.2-brightgreen)](https://spring.io/projects/spring-boot)
[![Vue 3](https://img.shields.io/badge/Frontend-Vue%203-blue)](https://vuejs.org/)
[![Vite](https://img.shields.io/badge/Build-Vite%205-646cff)](https://vitejs.dev/)
[![Three.js](https://img.shields.io/badge/3D-Three.js-black)](https://threejs.org/)

**点豆成金** 是一款结合了人工智能（AI）、像素艺术（Pixel Art）与 3D 体素建模的创意应用。它可以将您的文字心情、照片、3D 模型或股票收益截图，一键转化为精美的像素风作品，并提供专业的拼豆（Perler Beads）底稿方案。

---

## 📖 项目概述

本项目为单页 Web 应用（Vue 3 + Vite）配合 Spring Boot 后端，支持四类核心能力：

| 模块 | 名称 | 处理位置 | 是否依赖后端 | 核心服务 |
| :--- | :--- | :--- | :--- | :--- |
| **A** | **文字心情** | 前端 UI + 后端生图与像素化 | 是 | Agnes |
| **B** | **图片拼豆** | 本地 Canvas / 后端人像卡通化 | 卡通化时需要 | **Agnes Image** |
| **C** | **股票配图** | 浏览器内 OCR + 像素渲染 | 否 | Tesseract.js |
| **D** | **3D 拼豆** | 3D Voxel 变换 + TripoSR / 本地浮雕 | TripoSR 模式需要联网 | **TripoSR / Three.js / Canvas** |

---

## 🚀 核心功能详解

### 1. 文字心情 (Mood to Pixel)
*   **流程**：支持文案输入或 **Web Speech API 浏览器原生语音输入**。后端调用 Agnes 生成图片并自动像素化。
*   **特点**：自动根据语境追加“拼豆艺术”提示词，生成即底稿。

### 2. 照片拼豆 (Photo to Perler)
*   **人像卡通化**：后端调用 **Agnes Image** 图生图接口，把上传照片转成卡通风格，再由前端生成拼豆底稿。
*   **底稿映射**：支持 MARD、COCO 等主流品牌色号的一键映射与颗数统计。

### 3. 股票配图 (Stock Market Mood)
*   **高效率识别**：**[最新优化]** 采用了全新的单次 PSM 精准扫描策略，相比旧版提速 200%。
*   **离线识别**：纯前端 Tesseract.js OCR 解析盈亏截图，保护隐私。根据盈利/亏损状态自动匹配不同的像素风搞笑表情包。
*   **实时进度**：增加了 OCR 识别进度的百分比提示，处理逻辑不再“黑盒”。

### 4. 3D 拼豆 (3D Voxel Art)
*   **模型体素化**：上传 `.obj` 或 `.glb` 模型，实时进行 3D 体素化计算，支持逐层切片查看图纸。
*   **TripoSR 2D 转 3D**：前端直接调用 Hugging Face 上的 TripoSR Space，把单张照片生成 `.glb` 3D 模型，再交给浏览器体素切片。
*   **本地浮雕备用**：浏览器也可以根据照片颜色和明暗生成可切片的 3D 体素浮雕，不需要额外 GPU 服务。
*   **UI 隔离**：**[修复]** 切换标签时自动清理旧模式结果，防止 2D/3D 内容重叠粘连。

---

## 🛠️ 技术栈与架构

### 前端 (Frontend)
*   **框架**：Vue 3 (Composition API)、Vite 5
*   **3D 引擎**：Three.js (用于体素预览与空间计算)
*   **AI / 浏览器能力**：Web Speech API (语音)、TripoSR、Canvas 图像处理、Three.js 3D 渲染

### 后端 (Backend)
*   **核心**：Java 17、Spring Boot 3.2.5
*   **外部服务**：
    *   **Agnes AI**：文字生成图片、图片编辑/图生图、人像卡通化。

---

## ⚙️ 配置说明

### 后端配置

真实 API Key 不要写进代码，也不要上传到 GitHub。后端会从环境变量读取密钥：

```bash
export AGNES_API_KEY="你的 Agnes Key"
```

也可以参考根目录的 `.env.example`，但 `.env` 文件本身不要提交。

| 配置项 | 含义 | 示例 |
| :--- | :--- | :--- |
| `AGNES_API_KEY` | Agnes API 密钥 | `sk-xxxx` |
| `agnes.api-base` | Agnes 接口地址 | `https://apihub.agnes-ai.com/v1` |
| `agnes.text-model` | Agnes 文本模型 | `agnes-2.0-flash` |
| `agnes.image-model` | Agnes 图片模型 | `agnes-image-2.1-flash` |

---

## 📡 后端 API 接口

1.  `POST /api/mood-pixel`: 文字生拼豆。
2.  `POST /api/perler-cartoonize`: 使用 Agnes Image 图生图进行卡通化。

---

## 📦 本地开发

1. **后端**：`mvn spring-boot:run` (端口 8080)
2. **前端**：`pnpm install && pnpm run dev` (端口 5173，已配置代理)

---

> [!NOTE]
> **2D to 3D 提示**：TripoSR 模式不需要你配置 API Key，但它依赖 Hugging Face 公共 Space，可能会排队、变慢或临时不可用；本地浮雕模式不联网，但生成的是“照片浮雕式体素模型”，不是完整 AI 重建的可环绕 3D 模型。
>
> 本地开发时，TripoSR 通过 `frontend/vite.config.js` 里的 `/triposr` 代理访问。上线部署到 Vercel、Netlify、Nginx 等环境时，需要另外配置同等代理，或改成由 Java 后端中转 TripoSR。

---

*本项目由多人团队协作开发，同步了队友 xiangsu2 版本的最新 AI 绘图优化。*
