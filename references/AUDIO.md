# 配音与字幕

## 默认方式

Edge TTS 使用 zh-CN-YunxiNeural、-3% 语速，网络服务无需在本包配置密钥。文本按镜头合成，真实词级时间戳来自服务返回。文案、声音或语速变了会重做对应音频；不使用“文件已经存在就不管内容”的缓存。

音轨每镜前留 0.3 秒，末镜额外停留供看联系方式。时长自动按实际音频算，不能截断句尾。不要手工强行写固定 60 秒。

数字、缩写如被服务改写为另一种字面形式，先在 narration 中改为希望朗读的中文表达，再重新生成；不要删除“文本与时间戳一致”的校验。术语发音正确与否仍需试听。

## 国产/其他服务外部接口

在当前 WorkBuddy 环境通过已连接、已授权的语音工具生成每镜一个音频文件，或让用户提供音频。服务可以是国产 TTS、本地 TTS 或其他工具；本技能不虚构其 API。只把服务要求的文字发送过去，不上传整本手册。

将结果保存到项目目录，创建 `external-audio.json`，时间单位均为秒，相对该镜头音频开头（不要自己额外加 0.3 秒，脚本会处理）：

```json
{
  "scenes": {
    "hook": {
      "audio": "speech/hook.wav",
      "words": [
        {"text": "一张", "start": 0.12, "end": 0.45},
        {"text": "铜网", "start": 0.47, "end": 0.82}
      ]
    }
  }
}
```

上例只演示结构；实际 words 必须覆盖该镜头的全部配音且与 narration 完全一致（忽略标点）。每个 scene id 都要有一条记录。audio 可以是 WAV、MP3 或 FFmpeg 可读格式。words 必须来自 TTS 或真实音频对齐工具；不能照抄这组示例时间。

如果服务只有准确的分句时间戳，使用 `captions` 替代 `words`：

```json
{
  "scenes": {
    "hook": {
      "audio": "speech/hook.wav",
      "captions": [
        {"text": "一张铜网", "start": 0.12, "end": 0.82},
        {"text": "能让油通过吗？", "start": 0.95, "end": 2.10}
      ]
    }
  }
}
```

句级模式会整句高亮，不伪装逐词同步。音频无时间戳时先用已可用的 ASR/强制对齐服务生成并核对，不能靠按字数估时。只有音频但没有对齐能力时明确缺少这一步，不能交付声称已同步的版本。

```powershell
python "技能目录/scripts/pipeline.py" audio "项目目录/project.json" --out "项目目录/build" --external-audio "项目目录/external-audio.json"
python "技能目录/scripts/pipeline.py" preview "项目目录/project.json" --out "项目目录/build"
python "技能目录/scripts/pipeline.py" render "项目目录/project.json" --out "项目目录/build"
```

若用 `build` 也必须带 `--external-audio`，否则默认调用 Edge。再次调用 audio 时保持相同参数。

## 混音与署名

已内置：人声响度归一化、音乐频段让位、较低音乐响度、人声侧链压低、淡入淡出和限幅。默认音乐是 Kevin MacLeod 的 Inspired，许可和发布署名见 assets/MUSIC-LICENSE.txt。无需任何付费音乐账号。

程序报告音乐相对人声的中位电平差与整体 LUFS/真峰值；这不是听感保证，还需实际试听。目标约 -16 至 -18 LUFS、真峰值低于 -1 dBFS，音乐通常比说话时人声低 18–24 dB；自动检查接受范围略宽，避免把自然停顿当成故障。

署名不放视频画面；发布时把 publish-notes.txt 中的音乐署名放作品简介。文件元数据会写一份，但平台可能丢弃元数据，因此不要宣称只写元数据就一定满足所有发布场景。其他曲目先核实来源、作者、许可和商用条件，再改 path 与 credit。
