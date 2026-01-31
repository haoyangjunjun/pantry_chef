# 🥗 智能冰箱管家 - PantryChef

![PantryChef Banner](https://img.shields.io/badge/Pantry-Chef-4f46e5?style=for-the-badge&logo=flask)
![Python](https://img.shields.io/badge/Python-3.8+-blue?logo=python)
![SQLite](https://img.shields.io/badge/SQLite-003B57?logo=sqlite)

> **开发初衷：**
> 您是否也有这样的困扰：每次准备做饭，都要先跑到不在厨房的冰箱前统计食材数量？
> 为了解决这个痛点，也是在工作、学习和写毕设之余迸发的新鲜想法，我决定将其实践，开发了这款《智能冰箱管家》。它能将家庭库存与菜谱智能链接，解决您“冰箱里有什么”和“今天能吃什么”的两大世纪难题。

**PantryChef** 是一个专为家庭/个人设计的**私有化库存与菜谱管理系统**。界面精美、交互直观、纯本地数据，完美适配手机移动端。

## ✨ 核心特性 (Features)

*   **🧊 冰箱库存跟踪**：随时增减食材数量，一目了然。
*   **🍳 智能菜谱推荐**：根据当前库存，**自动筛选**并标记出“可烹饪（绿框）”或“部分食材不足（黄框）”的菜谱。
*   **📊 精确计量**：做菜再也不是“适量”。定义菜谱时可精确到“番茄需 2 个”，库存不足 2 个时将智能预警。
*   **🔖 自由档案管理**：支持 Emoji、自定义分类颜色和菜谱标签（如：🔥麻辣、⚡快手）。
*   **📝 Markdown 支持**：菜谱做法步骤支持标准 Markdown 语法排版。
*   **⚡ 极简极速**：Python Flask + SQLite 单文件无感部署，响应式设计，完美适配 PC 与 手机。

## 🛠️ 技术栈 (Tech Stack)

*   **后端**: Python Flask  
*   **数据库**: SQLite3 (纯本地文件，无需配置服务器)  
*   **前端**: HTML5 + CSS3 + 原生 JavaScript (无需 Node 环境，无编译构建)  

## 🚀 部署指南 (Deployment)

本项目特别推荐部署在闲置的 **Android 手机** (搭配 Termux) 作为家庭微型服务器。

### 💻 标准 PC 部署 (Windows/Mac/Linux)

1. 克隆代码库：
```bash
git clone https://github.com/haoyangjunjun/PantryChef.git
cd PantryChef
```

2. 安装依赖：
```Bash
pip install flask
```
3. 运行服务：
```Bash
python app.py
```
访问 http://localhost:5000 (局域网内可访问 http://[你的IP]:5000)

### 📱 Termux 手机部署指南 (推荐)
让您的闲置手机变身永久在线的家庭管家！  
1. 在手机下载安装 Termux。  
2. 安装 Python：`pkg install python git`  
3. 获取代码：`git clone https://github.com/haoyangjunjun/PantryChef.git`  
4. 启动防止休眠：`termux-wake-lock`  
5. 运行：`cd PantryChef && pip install flask && python app.py`

(进阶：配合 termux-services 与 Termux:Boot，可实现开机自启防杀后台，具体操作在本人博客中)

## 👨‍🍳 关于作者
开发者: haoyangjunjun & AI 助手  
让做饭变得更简单！  
Made with ❤️ for better cooking.