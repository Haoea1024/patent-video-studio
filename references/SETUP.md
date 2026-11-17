# 环境与 WorkBuddy 安装

## 安装技能包

WorkBuddy 官方文档支持“Skills → 添加技能 → 上传技能”导入本地包：
https://www.workbuddy.ai/docs/workbuddy/From-Beginner-to-Expert-Guide/Function-Description/Skills
核对日期：2026-11-17。不同客户端入口名称可能不同，以当前界面为准。

上传交付的 `patent-video-studio.zip`。ZIP 根目录是 SKILL.md、scripts、references、assets、examples，不要只上传 SKILL.md，否则程序、模板和音乐会缺失。不必手动修改 WorkBuddy 全局配置。若当前版本不接受 ZIP，将完整目录解压后让 WorkBuddy 按它当前支持的导入方式安装。不要猜固定配置目录。

## 所需能力

Agent 能读本地文件、编辑 JSON、执行 Python 和打开图片。无需访问微信或获取旧会话。Python 3.10+；开发实测 Windows/Python 3.14，其他平台属于代码层面可移植，未实测。Windows 下优先使用已安装的宋体与微软雅黑。macOS/Linux 需能显示中文的宋体类/黑体类字体；不随包分发系统字体。

在技能文件夹中执行（路径有空格要加引号）：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m playwright install chromium
.\.venv\Scripts\python.exe scripts/pipeline.py doctor
```

这是一次性环境准备。若技能安装目录只读，在用户工作目录建立 `.venv`，用绝对路径指定 requirements.txt 和 pipeline.py。以后始终使用同一个 Python 解释器，不要安装到 A 环境、运行在 B 环境。macOS/Linux 的解释器为 `.venv/bin/python`。已有依赖时无需再建环境。网络受限时使用单位认可的 PyPI/Playwright 镜像或已有软件，不能绕过权限。

`requirements-tested.txt` 记录开发机实际验证过的版本；在兼容的 Python 上可用它复现。若指定版本无法从当前镜像获得，使用 requirements.txt 的兼容范围，并重新运行 doctor 和示例预览。Windows 旧默认编码环境可在 Python 后加 `-X utf8`，本包的文本读写本身均明确使用 UTF-8。

脚本自动寻找 Playwright Chromium，再尝试系统 Edge/Chrome；也可设置 `PATENT_VIDEO_CHROME` 为浏览器可执行文件绝对路径。FFmpeg 由 imageio-ffmpeg 提供，可用 `PATENT_VIDEO_FFMPEG` 覆盖。无需给 FFmpeg 单独加 PATH。每次升级 Playwright 后可能需要重新安装对应浏览器。

字体检查结果只是浏览器 API 的提示，缺字最终要看预览图。出现方框先修字体，不要用空白图片代替字幕。

## 快速验证

在任意有写权限的工作目录（不是技能目录）运行：

```powershell
python "技能目录/scripts/pipeline.py" init --example mesh --out "测试项目"
python "技能目录/scripts/pipeline.py" validate "测试项目/project.json" --out "测试项目/build"
python "技能目录/scripts/pipeline.py" audio "测试项目/project.json" --out "测试项目/build"
python "技能目录/scripts/pipeline.py" preview "测试项目/project.json" --out "测试项目/build"
```

核对样例资料与预览，再设 review 为 true。重新跑 audio 后 render。首次语音需要网络，生成约一分钟的视频通常还需要数分钟处理，以机器实际性能为准。

## 可直接发给 WorkBuddy 的指令

> 使用 patent-video-studio，根据我提供的专利 PDF 制作一条 9:16 中文宣传视频。先读 SKILL.md，使用内置脚本与模板，不要重写渲染器。面向潜在合作企业，沿用三个样片的深蓝、宋体、琥珀色风格。先核对事实和已做项目，再填 project.json。完成配音、真实时间戳字幕、轻背景音乐、独立封面和 MP4，跑完检查再交付。资料里找不到的信息不要编。

若想同时测试国产工具链，追加：

> 配音和绘图也仅使用当前已配置的国产服务，不使用 Edge TTS；按 AUDIO.md 准备 external-audio.json。无法调用时准确说明缺少的服务，不假装已经生成。

## 网络和数据边界

PDF 提取、动画、视频编码、检查在本地进行；默认 Edge TTS 只发送各镜头配音文本，不发送完整专利 PDF。外部绘图/语音工具按其接口接收所提交内容。没有密钥写入技能包，不扫描其他文件寻找密钥，不改平台权限，不自动安装插件，不自动发布。

官方技术资料：
- https://playwright.dev/python/docs/browsers
- https://github.com/rany2/edge-tts

## 典型故障

- `ModuleNotFoundError`：用实际运行脚本的 Python 安装 requirements。
- 浏览器缺失：运行 `python -m playwright install chromium`，或使用已装 Edge/Chrome。
- Edge 超时/鉴权变化：最多三次重试，转 AUDIO 的外部接口；不要连续几十次调用。
- `Project changed`：配置变更后重新 audio，再 preview/render，不能删哈希校验。
- `Output belongs to another project`：新建输出文件夹；不覆盖别的项目。
- 乱码或标题溢出：修字体或缩短文案；不无限缩小到手机看不清。
- 没有图像生成插件：留空 cover.image，使用程序排版封面；不要填写不存在的路径。
- WorkBuddy 只说完成但无文件：检查实际输出目录和 validation.json，文件没生成就是没完成。
