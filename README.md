# FlowTodo RinUI

FlowTodo 的 PySide6 + QML 原生迁移版本。主窗口不再依赖 WebEngine，界面基于
[RinUI](https://github.com/RinLit-233-shiroko/Rin-UI)（Fluent Design 风格 UI 库），
业务逻辑通过 `BackendBridge` / `RinUIBackend` 复用既有 JSON 数据层，保持与旧版本
数据完全兼容。

## 功能

- 今日任务、任务流、项目、专注模式
- 任务流 / 项目编辑器
- 任务流启动准备、项目启动准备、专注进行页
- AI 规划、长期计划预览、账户统计、每日启动页
- RinUI / Class Widgets 主题、系统明暗模式、窗口材质
- AI 接口配置、开机启动、数据目录设置、灵动岛

新旧版本共享 `%LOCALAPPDATA%\FlowTodo\data`，已有 JSON 数据无需转换。

## 技术栈

| 组件 | 说明 |
| --- | --- |
| Python | 3.9+（Windows） |
| PySide6 | Qt 6 官方 Python 绑定，>= 6.11.1 |
| QML | 界面声明语言（`qml/` 目录） |
| RinUI | Fluent Design 风格 QML UI 库（已随仓库 vendored 到 `vendor/RinUI`） |
| darkdetect | 系统明暗模式检测 |
| pywin32 | Windows 平台能力（窗口 / 原生集成） |

## 运行方式

```powershell
# 1. 安装依赖
pip install -r requirements.txt

# 2. 启动应用
python .\app.py
```

> 说明：`app.py` 会优先从项目内 `vendor/` 目录加载 RinUI（已随仓库提交，
> 保证克隆后开箱即用）。如需改用 pip 安装的 RinUI，可执行
> `pip install "RinUI>=0.4.2"`，或删除 `vendor/` 后以普通方式安装依赖。

## 目录结构

```
FlowTodo_RinUI/
├── app.py               # 入口：加载 vendor/RinUI 并启动 QML 窗口
├── main.py              # 主业务逻辑（任务流 / 项目 / 专注 / AI 规划等）
├── compat_backend.py    # RinUI 后端桥接（QML <-> Python）
├── backend.py           # 业务后端
├── island.py            # 灵动岛逻辑
├── qml/                 # QML 界面
├── vendor/RinUI/        # RinUI 库（运行时依赖，MIT License）
├── requirements.txt     # Python 依赖
└── CLASS_WIDGETS_2_LICENSE.txt  # Class Widgets 2 设计参考的 MIT 许可证
```

## 许可证

- 本项目代码：开源发布（许可证见仓库 LICENSE 说明）。
- 第三方组件：
  - RinUI：MIT License，见 `vendor/LICENSE`（Copyright (c) 2025 RinLit）。
  - Class Widgets 2 设计参考：MIT License，见 `CLASS_WIDGETS_2_LICENSE.txt`。

## 更新日志 / Changelog

### v1.0.2（2026-08-18）

- **修复插件安装后 FlowTodo 不启动的问题**：旧版 launcher 尝试用插件目录下的 Python 环境启动 `app.py`，但插件包内不包含 `.venv`，回退到系统 `pythonw` 又缺少 PySide6，导致进程静默秒退。
- 新版 launcher 优先使用 FlowTodo 项目目录自带的 `.venv`（依赖齐全）启动 `app.py`，找不到项目目录时才回退插件目录；防重启动检测同时匹配项目目录与插件目录两种来源，避免重复拉起。
- 该修复已在本地 CW2 环境验证：插件加载后 FlowTodo 正常启动并保持存活。

### v1.0.1（2026-08-18）

- 首次接入 Class Widgets 2 插件广场自动发布流程，打包发布 `com.flowtodo.plugin`。

## 自动发布 / Auto Release

本仓库已接入 Class Widgets 2 插件官方发布流程（GitHub Actions），推送 `v*.*.*` 格式的 tag 时自动完成打包与发布：

1. 推送 tag：
```bash
git tag v1.0.2
git push origin v1.0.2
```

2. 在仓库 Settings → Secrets and variables → Actions 中配置 `CWPT_TOKEN`（从 [插件广场控制台](https://plaza.cw.rinlit.cn/console) 获取的发布令牌）

3. GitHub Actions 会自动：
   - 使用 `cw-plugin-pack` 打包插件，生成 `.cwplugin` 和 `.zip` 两种格式
   - 通过 `cw-plugin-publish` 自动发布到插件广场
   - 生成 changelog 并创建 GitHub Release 上传发布包
