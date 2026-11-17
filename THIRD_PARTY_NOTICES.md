# 第三方素材与引用

## 背景音乐

本仓库分发的 `assets/Inspired.mp3` 为 Kevin MacLeod 的 **Inspired**，使用独立的 **CC BY 4.0** 许可。

- 作者：Kevin MacLeod / incompetech.com
- 原始曲目：https://incompetech.com/music/royalty-free/index.html?isrc=USUAN1600022
- 许可：https://creativecommons.org/licenses/by/4.0/
- 仓库中的 MP3 为原始曲目；生成的视频会截取、均衡、淡入淡出，并在人声出现时压低音乐。
- 发布视频时，把生成的 `publish-notes.txt` 中署名放进作品简介。视频元数据也包含署名，但平台可能不保留元数据。

这项许可只覆盖音乐，不自动覆盖本仓库的代码、文档或其他素材。

## 专利示例与图片

三个示例依据对应专利及项目资料整理，来源列在 `examples/*.json` 中。示例封面为生成式图像，分镜缩略图来自样片画面。图中的结构、液体颜色、信号和温度分布均为示意，不是实验测量数据。

示例中出现的机构名称、专利及联系方式用于解释相应技术案例，不表示该机构对本软件的背书，也不授予专利实施权。本仓库不分发原始完整专利手册、私人聊天或账号凭据。

## 软件依赖

Python 依赖通过 `requirements.txt` 安装，浏览器通过 Playwright 安装。此仓库不打包这些依赖的可执行文件；各依赖保留其自身许可证，FFmpeg 的具体许可以实际取得的构建为准。

## README 组织参考

参考了 [Anthropic Skills](https://github.com/anthropics/skills) 的按使用方式组织文档、[Remotion](https://github.com/remotion-dev/remotion) 的效果先行、[yt-dlp](https://github.com/yt-dlp/yt-dlp) 的安装与依赖说明。未复制它们的代码、品牌图片或 README 正文；本项目也不依赖这些项目。
