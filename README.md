# KanaHover

**Windows 离线日语阅读助手 · Windows向けオフライン日本語読解ツール · Offline Japanese Reading Helper for Windows**

[简体中文](#简体中文) · [日本語](#日本語) · [English](#english)

**版本 / Version:** 0.7.1 · 2026-11-04 · Windows x64

> **⚠️ 重要 / Important:** 普通自动取词在必要时会模拟 Ctrl+C 并临时使用剪贴板，频繁复制、粘贴时请暂停工具。  
> 自動文字取得では Ctrl+C とクリップボードを使用する場合があります。コピー・貼り付けが多いときは一時停止してください。  
> Automatic selection may simulate Ctrl+C and use the clipboard. Pause KanaHover during copy/paste-intensive work.

---

## 简体中文

### 项目简介

KanaHover 是一款 Windows 日语阅读辅助工具。选中网页、编辑器或办公软件中的日语后，它会尝试显示**原文及对应的平假名**；也可以使用截图 OCR 识别无法直接选中的文字，并通过本地 OpenJTalk 朗读日语原文。

例如：**端末識別番号 → たんまつしきべつばんごう**。

工具以离线运行、尽量减少对当前工作的干扰为目标。**当前版本没有翻译功能**；翻译功能可能以后作为独立分支开发。

### 功能一览

| 功能 | 说明 |
| --- | --- |
| 自动取词 | 支持尝试读取 Chrome、Edge、Excel、WPS、Notepad、EmEditor 中选中的日语文字；兼容性取决于具体控件 |
| 假名显示 | SudachiPy + Sudachi Core 词典注音，支持片假名转平假名 |
| 弹窗 | 原文和假名分两行显示；显示时尽量不改变原软件的焦点 |
| 弹窗操作 | 可以主动点击、选中文字并使用 Ctrl+C 复制；单击框外关闭 |
| 截图 OCR | 默认 Alt+C，左键拖选区域，松开执行本地 OCR；Esc 或右键取消 |
| 离线朗读 | 点击扬声器朗读**日语原文**，再次点击停止，语速可选 0.8× / 1.0× / 1.2× |
| 暂停与恢复 | 托盘首行显示当前状态；暂停后停止自动取词，也无法启动新的截图 OCR |
| 开机启动 | 托盘 `Start with Windows` 选项为当前用户设置或取消登录自启动 |
| 便携版 | EXE 加 `_internal` 依赖文件夹，目标电脑不需要单独安装 Python / OCR / TTS 引擎 |

### 使用方法

**启动：** 下载完整的 Windows 便携版目录，双击 `KanaHover.exe`。请不要将 EXE 与 `_internal` 文件夹分开。程序主要运行在 Windows 系统托盘中。

**鼠标选词：** 在支持的程序中拖选日语，或者双击选中一个单词。成功获取选区时会显示原文与读音。对于 Excel/WPS，选中整个单元格**不等于**进入编辑模式后选中几个文字；部分编辑控件可能无法自动识别。

**截图 OCR：**
1. 按 `Alt+C` 进入截图模式。
2. 鼠标左键按住并拖出包含日语的矩形。
3. 松开左键结束截图，执行本地 OCR 并显示假名。
4. 截图时按 `Esc` 或右键取消。
5. 在托盘 `OCR Shortcut...` 中可以修改组合快捷键。

**朗读和复制：** 点击弹窗扬声器朗读上方日语原文，再次点击停止。主动点击弹窗内部后可以选中文字并按 Ctrl+C 复制；点击弹窗外任意位置的鼠标左键关闭。

### 系统托盘菜单

| 菜单 | 作用 |
| --- | --- |
| `暂停取词（当前：运行中）` | 点击暂停；暂停时变成 `开始取词（当前：已暂停）` |
| `开始取词（当前：已暂停）` | 点击恢复自动取词 |
| `Start with Windows` | 勾选/取消登录后自动启动 |
| `Test Popup` | 测试假名弹窗 |
| `OCR Shortcut...` | 设置截图快捷键 |
| `Voice Speed` | 选择 0.8×、1.0×、1.2× |
| `Restart` / `Exit` | 重启 / 完全退出 |

### ⚠️ 剪贴板与复制粘贴注意事项

**如果你的工作需要大量复制、粘贴、操作 Excel/WPS 表格或代码，请先通过托盘菜单暂停 KanaHover。**

自动取词优先调用 **Windows UI Automation**；当目标软件没有提供可读取的文字选区时，程序在部分鼠标选择场景下会尝试备用方式：**模拟 Ctrl+C → 读取系统剪贴板 → 尝试恢复原有剪贴板对象**。

**剪贴板恢复不是百分之百可靠。** 在连续快速复制、复杂表格格式、其他软件同时操作剪贴板等情形下，可能造成剪贴板内容或格式变化，或影响原本的 Ctrl+C / Ctrl+V 操作。

建议频繁复制时选择“暂停取词”，完成工作后再“开始取词”。暂停状态下新的截图 OCR 操作也会被禁用。**Alt+C 截图 OCR 本身不使用剪贴板。**

### 离线架构和已知限制

| 模块 | 实现 |
| --- | --- |
| UI / 托盘 | Python、Tkinter、pystray |
| 文字选取 | Windows UI Automation、Windows API、剪贴板备用方式 |
| 分词/读音 | SudachiPy、`sudachidict_core` |
| 截图 OCR | Pillow、Tesseract、日语 OCR 语言模型 |
| 朗读 | `pyopenjtalk-plus`、OpenJTalk / HTS 本地语音 |
| 快捷键与 Windows 集成 | keyboard、pywin32 |
| 打包 | PyInstaller 目录模式，EXE + `_internal` |

OCR、假名分析和日语朗读在本地完成，不调用云端 OCR/TTS/翻译服务，没有自动上传截图或云同步功能。但操作系统和其他应用可能独立使用剪贴板或剪贴板历史。

已知局限：某些程序无法读取选中文字；OCR 可能识别错字；专有名词、多音汉字、缺乏上下文时读音可能不准确。OpenJTalk 在安装路径包含中文等非 ASCII 字符时，可能需要将内置字典和音色复制到用户本地的纯英文临时缓存目录，首次朗读稍慢且会占用少量额外磁盘空间。

### 源码目录与构建

~~~text
main.py                   程序入口、选词、弹窗、托盘
ocr_feature.py            截图 OCR / 快捷键
speech_feature.py         语音播放
openjtalk_assets.py       字典和音色的路径处理
startup_feature.py        Windows 开机启动
app_paths.py              工程/打包运行时路径
version.py                版本信息
requirements.txt          依赖清单
requirements.lock.txt     构建时记录的包版本
KanaHover.spec            PyInstaller 构建配置
scripts/setup_vendor.ps1  项目本地依赖准备
scripts/build.ps1         便携版打包
tessdata/                 OCR 语言文件
vendor/python/            项目内 Python 依赖、日语词典、语音资源
vendor/tesseract/         Tesseract EXE 和 DLL
releases/                 构建产物（不提交普通 Git）
README.md
~~~

开发环境目前基于 Windows x64 + Python 3.14。准备依赖、运行源码和打包：

~~~powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup_vendor.ps1
python .\main.py

python -m pip install pyinstaller
powershell -ExecutionPolicy Bypass -File .\scripts\build.ps1
~~~

依赖准备脚本会将 Python 包安装到 `vendor/python`。Tesseract 部分需要构建机上已安装 Tesseract，脚本才可复制其运行文件和 DLL。日语 OCR 模型也需放在 `tessdata`。**克隆源代码不一定就包含全部大型离线模型。**

### GitHub 发布、vendor 与依赖获取

本仓库建议只提交**源码、README、配置、依赖定义与构建脚本**。`vendor/python/` 和 `vendor/tesseract/` 默认由 `.gitignore` 排除，因为包含大量第三方二进制包、字典和模型；`releases/` 也不加入 Git 历史。

面向普通用户，请使用 **GitHub Releases** 发布完整便携版压缩文件（EXE + `_internal`），而不是把几百 MB 依赖直接放进源码仓库。请在公开二进制前确认第三方依赖、词典和音色的许可与再分发条件。

**如果你需要 `vendor` 目录中的相关依赖包或资源文件，可联系：riecardx@gmail.com。** 请说明需要的组件及使用目的；是否可以共享仍须遵守各组件的许可证。

正式公开源码前，请为 KanaHover 添加明确的 `LICENSE`，同时检查 Tesseract、Sudachi 词典、OpenJTalk 音色、OCR 模型与各 Python 库的授权和署名要求。

### 反馈与维护

欢迎提交 GitHub Issues / Pull Requests。建议附上 Windows 版本、目标软件、具体操作、期望结果和实际结果；发布日志或截图前请删除敏感信息。后续可能改进无剪贴板取词、WPS/Excel 兼容、OCR 准确率、打包体积和自动化测试。

**源码与已打包 EXE 可能不同步。** 修改源码后需要重新打包，建议在无 Python 环境的 Windows 电脑上验证发行版。

---

## 日本語

### 概要

KanaHover は Windows のタスクトレイで動作するオフライン日本語読解支援ツールです。選択した日本語の**原文とひらがなの読み**をポップアップ表示し、スクリーンショット OCR と OpenJTalk による日本語音声読み上げにも対応します。

例：**端末識別番号 → たんまつしきべつばんごう**。

現在、**翻訳機能はありません**。将来は別ブランチで検討する可能性があります。

### 主な機能

| 機能 | 内容 |
| --- | --- |
| 選択文字の取得 | Chrome、Edge、Excel、WPS、Notepad、EmEditor で選択した文字の取得を試みます。動作はコントロールによって異なります |
| ふりがな | SudachiPy と Sudachi Core 辞書による漢字の読み取得、カタカナからひらがなへの変換 |
| ポップアップ | 原文と読みを2行で表示。表示時に作業中のフォーカスをできるだけ維持 |
| 選択とコピー | ポップアップ内の文字を選択して Ctrl+C でコピー。外側を左クリックすると閉じます |
| OCR | `Alt+C` → 左ドラッグ → ボタンを離して確定。`Esc` / 右クリックでキャンセル |
| 音声 | 日本語原文のみ OpenJTalk で朗読。再クリックで停止。速度 0.8× / 1.0× / 1.2× |
| 一時停止 | トレイ先頭で状態を表示。一時停止すると自動取得と新しい OCR 操作を無効化 |
| 自動起動 | `Start with Windows` でユーザーのログイン時自動起動を設定 |
| ポータブル | EXE と `_internal` のセット。利用者側で Python 等の個別インストールは不要 |

### 使い方とトレイメニュー

1. 配布フォルダーを丸ごと解凍し、`KanaHover.exe` を実行します。`_internal` は削除しないでください。
2. 対応アプリ上で文字をドラッグ選択または単語をダブルクリックします。Excel/WPS ではセルの選択と**編集中の文字の選択**は異なります。
3. 選択できない文字は `Alt+C` のスクリーンショット OCR で取得します。`Esc` または右クリックでキャンセルします。
4. ポップアップのスピーカーボタンで原文を読み上げます。内部の文字はクリックして選択・コピーできます。
5. トレイを右クリックして各設定を操作します。

| メニュー | 動作 |
| --- | --- |
| 先頭行（中国語） | `暂停取词（当前：运行中）`＝一時停止、`开始取词（当前：已暂停）`＝再開 |
| `Start with Windows` | ユーザーのログイン時自動起動 |
| `Test Popup` | ポップアップ表示テスト |
| `OCR Shortcut...` | OCR ショートカット設定 |
| `Voice Speed` | 0.8×、1.0×、1.2× |
| `Restart` / `Exit` | 再起動 / 終了 |

### ⚠️ クリップボードについて

**頻繁にコピー・貼り付けを行う場合、必ずトレイで KanaHover を一時停止することを推奨します。**

自動文字取得では、まず Windows UI Automation を使用します。選択文字が取得できない場合は、状況に応じて **Ctrl+C を模倣してクリップボードの内容を読み取り、以前の内容の復元を試みます**。しかし**復元は保証されません**。Excel/WPS の書式情報や連続コピー、他のアプリによるクリップボード操作と干渉する場合があります。

一時停止中は自動取得と新しいスクリーンショット OCR を利用できません。画面 OCR 自体はクリップボードを使用せず、画像を直接処理します。

### オフライン構成・開発

日本語解析には SudachiPy / `sudachidict_core`、OCR には Pillow / Tesseract、音声には `pyopenjtalk-plus` / OpenJTalk / HTS を使用しています。通常の処理でクラウド OCR、TTS、翻訳 API は使いません。スクリーンショットの自動アップロード・クラウド同期もありません。OCR や辞書による読みの判定は完全ではありません。

Windows x64 / Python 3.14 環境での準備、ソース起動、ビルド：

~~~powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup_vendor.ps1
python .\main.py

python -m pip install pyinstaller
powershell -ExecutionPolicy Bypass -File .\scripts\build.ps1
~~~

`vendor/python` には Python 依存パッケージ・日本語辞書・音声データを、`vendor/tesseract` には OCR 実行ファイルと DLL を置きます。Tesseract の準備にはビルド用 PC へのインストールが必要です。`tessdata` には日本語 OCR モデルが必要です。大容量のバイナリは Git 管理から除外されているため、**ソースの clone だけではすべての依存データが揃いません**。

### GitHub 配布と vendor の入手

GitHub リポジトリにはソース、ドキュメント、依存定義、ビルドスクリプトを登録し、完成したポータブル版は **GitHub Releases** に掲載する方針を推奨します。大容量の `vendor` バイナリを通常の Git 履歴に含めない構成です。

**`vendor` フォルダー内の依存パッケージやリソースが必要な方は、riecardx@gmail.com までご連絡ください。** 必要なコンポーネントと利用目的をお知らせください。実際の共有には各コンポーネントのライセンス条件が適用されます。

ソース公開前に KanaHover 自身の `LICENSE` を追加し、Sudachi 辞書、OCR モデル、OpenJTalk 音色、Tesseract、各 Python ライブラリの再配布条件を確認してください。

### 制限・開発協力

対応ソフトでも選択文字を取得できない場合があります。OCR や読みの解析は固有名詞・多音字・画像品質によって誤ることがあります。ポータブル版の EXE を移動した場合は自動起動の再登録が必要なことがあります。また、ソースの変更は旧 EXE に自動反映されません。

Issues / Pull Requests を歓迎します。Windows バージョン、対象アプリ、再現手順、期待結果と実際の結果をお知らせください。ログ等の個人情報は公開前に削除してください。

---

## English

### Overview

KanaHover is an offline Japanese reading helper for Windows. It displays the **selected Japanese text and its hiragana reading**, offers local screenshot OCR, and speaks the original Japanese using OpenJTalk.

Example: **端末識別番号 → たんまつしきべつばんごう**.

**Translation is not included** in the current branch; it may be developed separately later.

### Features

| Feature | Description |
| --- | --- |
| Selection reading | Attempts to read highlighted text in Chrome, Edge, Excel, WPS, Notepad and EmEditor; compatibility varies |
| Hiragana | SudachiPy / Sudachi Core dictionary for Japanese readings and katakana conversion |
| Popup | Original Japanese and hiragana on separate lines; avoids intentionally stealing focus |
| Copy and dismiss | Click inside to select and Ctrl+C copy; left-click outside to dismiss |
| Screenshot OCR | Press `Alt+C`, drag with the left mouse button, release to recognize; `Esc` or right-click cancels |
| Local speech | OpenJTalk speaks **the Japanese original only**; click again to stop; speeds: 0.8×, 1.0×, 1.2× |
| Pause/resume | Tray menu shows current status; pausing disables automatic selection and new OCR captures |
| Startup | `Start with Windows` toggles per-user Windows login startup |
| Portable release | EXE + `_internal`; no separate Python, OCR or TTS installation on the target PC |

### Getting started

1. Download and unpack the **entire** portable release folder. Double-click `KanaHover.exe`. Do not remove `_internal`.
2. Drag-select Japanese text or double-click a word in a supported application. Excel/WPS cell selection is not the same as highlighting a substring in cell-edit mode.
3. For text that cannot be selected, press `Alt+C`, drag a capture rectangle and release the left button. `Esc` and right-click cancel.
4. Click the popup speaker icon to speak the original Japanese. Click again to stop. Popup text can be selected and copied.
5. Right-click the Windows tray icon for pause/resume, shortcut, speech speed and startup settings.

### Tray menu

| Item | Purpose |
| --- | --- |
| First entry (Chinese status text) | `暂停取词（当前：运行中）` = Pause; `开始取词（当前：已暂停）` = Resume |
| `Start with Windows` | Toggle per-user login startup |
| `Test Popup` | Test the popup |
| `OCR Shortcut...` | Change OCR hotkey |
| `Voice Speed` | 0.8×, 1.0×, 1.2× |
| `Restart` / `Exit` | Restart / quit |

### ⚠️ Clipboard warning

**Pause KanaHover during frequent copying, pasting, spreadsheet editing or code work.**

Automatic selection first tries Windows UI Automation. If the target control does not expose a readable selection, the fallback may **simulate Ctrl+C, inspect the Windows clipboard, and attempt to restore the previous clipboard object**.

**Clipboard restoration is best-effort, not guaranteed.** This can interfere with normal copy/paste, particularly with complex Excel/WPS cell formats, rapid repeated copying, or other applications accessing the clipboard.

Use the first tray menu entry to **Pause** before copy-heavy tasks, then **Resume** afterward. Pausing also prevents new screenshot captures. Screenshot OCR itself does not use the clipboard.

### Technical architecture

| Component | Technology |
| --- | --- |
| UI and tray | Python, Tkinter, pystray |
| Automatic selection | Windows UI Automation / Windows APIs / clipboard fallback |
| Japanese readings | SudachiPy and `sudachidict_core` |
| OCR | Pillow, Tesseract and Japanese OCR language data |
| Speech | `pyopenjtalk-plus` / OpenJTalk / HTS |
| Windows integration | pywin32, keyboard |
| Distribution | PyInstaller onedir (EXE + `_internal`) |

Readings, OCR, and speech are processed locally, without cloud OCR/TTS/translation APIs or automatic screenshot uploads. OCR may make mistakes; names, ambiguous kanji and missing context may also result in incorrect readings.

OpenJTalk may copy its bundled dictionary and voice to an ASCII-only local temporary cache to work around native filename limitations. The initial playback can take longer and use additional disk space.

### Building from source

Development currently targets Windows x64 with Python 3.14.

~~~powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup_vendor.ps1
python .\main.py

python -m pip install pyinstaller
powershell -ExecutionPolicy Bypass -File .\scripts\build.ps1
~~~

The project stores Python packages, dictionary data and OpenJTalk assets in `vendor/python`, Tesseract executable/DLL files in `vendor/tesseract`, and OCR language files in `tessdata`. The setup script expects Tesseract to be installed on the **build machine** so its runtime files can be copied. Large vendor binaries are ignored by Git; **cloning this repository alone may not provide every offline resource**.

Main files include `main.py`, `ocr_feature.py`, `speech_feature.py`, `openjtalk_assets.py`, `startup_feature.py`, `app_paths.py`, `version.py`, `requirements.txt`, `requirements.lock.txt`, `KanaHover.spec`, and the `scripts/` build helpers.

### Publishing on GitHub and requesting vendor files

The recommended approach is to put **source code, documentation, dependency manifests, and build scripts** in the GitHub repository, while distributing the assembled portable app through **GitHub Releases**. Large `vendor` binaries, generated releases, personal settings and logs are excluded from normal Git tracking.

**Need packages or resources from the `vendor` directory? Contact riecardx@gmail.com.** Please identify the components and intended use. Availability and redistribution remain subject to the licenses of the respective third-party packages.

Before making a public release, add an explicit `LICENSE` for KanaHover itself and review the licensing and attribution requirements for Sudachi dictionaries, Tesseract, OCR models, OpenJTalk voices, and Python dependencies.

### Limitations and contributions

Not every application exposes its selected text. Clipboard fallback may interfere with copying; pause when necessary. OCR and dictionary readings can be wrong. Moving the portable folder may require re-registering Windows startup. Source modifications do not automatically update previously built EXEs.

Issues and pull requests are welcome. Include your Windows version, target application, reproduction steps, expected and actual results, and remove sensitive information from any logs or screenshots.

---

*KanaHover is an evolving open-source project. / KanaHover は継続的に開発されるプロジェクトです。 / KanaHover 将持续维护与改进。*
