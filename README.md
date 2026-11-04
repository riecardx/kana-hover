# KanaHover

Windows 日语取词、假名显示、截图 OCR 和离线 OpenJTalk 朗读工具。

**当前版本：0.7.1 — 2026-11-04**

## 功能

- Chrome、Edge、Excel、WPS、Notepad、EmEditor 中鼠标选择日语时显示原文与假名。
- 自动取词优先 UI Automation，必要时使用剪贴板备选路径（**保留现有行为**）。
- Alt+C 截图 OCR：左键拖选，松开识别；Esc/右键取消；托盘可修改快捷键。
- 弹窗不主动抢焦点；在框内可以选中文字并按 Ctrl+C；点击框外关闭。
- OpenJTalk 本地日语朗读，点击扬声器开始，再次点击停止，托盘可选择语速。
- v0.7.1 修复 HTS 在含中文的安装路径下无法打开音色的问题；首次朗读会将内置语音字典/音色复制到当前用户 TEMP 的 ASCII 路径缓存（约 100 MB），不联网。
- 首行菜单显示取词运行/暂停状态。
- 托盘新增 **Start with Windows**：勾选后在当前 Windows 用户登录时启动；再次点击取消勾选。

## 工程目录

```text
kana-hover/
  main.py                  程序入口
  app_paths.py             便携版和源码运行路径
  ocr_feature.py           截图 OCR
  speech_feature.py        OpenJTalk 语音
  startup_feature.py       Windows 登录自启动
  requirements.txt         Python 依赖清单
  tessdata/                日语与英语 OCR 数据
  vendor/
    python/                项目内 Python 第三方包（含 Sudachi 词典与 OpenJTalk 字典/音色）
    tesseract/             项目内 Tesseract 可执行文件与 DLL
  scripts/
    setup_vendor.ps1       依赖准备
    build.ps1              生成便携版
  KanaHover.spec           PyInstaller 目录模式配置
  .gitignore
```

## 开发环境

工程依赖保存在 **vendor/** 中。开发环境需 Windows x64 + Python 3.14：
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup_vendor.ps1
python .\main.py
```
在源代码模式中，`app_paths.prepare_local_imports()` 优先引用项目目录的 `vendor/python`，OCR 执行项目内 `vendor/tesseract/tesseract.exe`。需 Python 标准库和 Tkinter。

## 制作无需 Python 环境的便携版

在项目根目录运行：
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\build.ps1
```

输出目录：`releases/KanaHover-0.7.1-20261104/`，包含 `KanaHover.exe` 与 `_internal/` 依赖文件夹；不能只复制 EXE 而不复制整个目录。目标 Windows 需要允许普通桌面程序运行，不依赖系统安装 Python/Tesseract/日语语音包。当前 EXE 构建**未在干净 Windows 系统试运行**。

项目设置文件会写入 EXE 所在目录：`ocr_settings.json` 和 `voice_settings.json`。如放在无写入权限的目录，设置可能保存失败；建议放在用户可写的目录。

登录自启动使用 `HKCU\Software\Microsoft\Windows\CurrentVersion\Run`，无需管理员权限。请先将便携版移动至最终位置，再启用此功能，否则移动文件夹后需要重新注册。

## 发布与授权须知

Python 包存放于工程内供离线使用。Git 默认忽略体积巨大的 `vendor/` 二进制资源，源码克隆后运行 `setup_vendor.ps1` 重建；如希望把它们一起放进 Git，需要 Git LFS 或单独发布资源档案。

在对公众分发前，请逐项检查 Tesseract、Sudachi/词典、OpenJTalk/语音模型、PyInstaller、Windows 运行库与其他依赖的开源许可和归属声明，不能仅凭技术上可打包就推定可以任意再分发。
