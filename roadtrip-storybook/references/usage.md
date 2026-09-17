# 安装、复用与批量使用

把分享ZIP解压后，将整个 `roadtrip-storybook` 文件夹放到接收者的个人技能目录。Codex默认 `~/.codex/skills/roadtrip-storybook`；Windows通常为 `%USERPROFILE%\.codex\skills\roadtrip-storybook`。若设置了 `CODEX_HOME`，使用其下的 `skills`。其他支持SKILL.md的代理，按该工具实际支持的目录安装；核心构建器与特定代理无关，各产品自动发现行为可能不同。

保持各子目录关系。已有同名技能时先比较版本，不直接覆盖。Codex在后续回合发现技能；若尚未显示，可以显式提供SKILL.md路径读取。

## 给代理的用法

```text
使用 $roadtrip-storybook，把附件的旅行MD做成可翻页手绘旅行手账。
保留已确认和待确认安排，桌面半页地图，小车沿路移动，输出可离线打开的HTML。
```

```text
使用 $roadtrip-storybook，分别读取这5份行程，给每份做一本同风格HTML，
放到指定输出目录。天数、交通方式、人数和宠物以各自资料为准。
```

代理先理解资料并整理JSON，再运行构建。构建器不是任意MD的自动理解器；脱离代理时，应自己按数据格式填写JSON。

## 命令行

```text
python /path/to/roadtrip-storybook/scripts/build.py --batch ./inputs --out-dir ./output
```

Python 3.9+标准库构建，无需联网。`--check` 只预检；更新已授权输出时加 `--force`。验证失败返回非零退出码，并指出文件和字段。单份生成用 `--input` 与 `--output`。

每份HTML自带样式、路线图、数据和动画脚本，无需服务器或API密钥。支持左右键、目录、手机轻扫、暂停和重播。清单状态按旅行id隔离，在当前浏览器本地保存，不会同步给同行人。

## 开源依赖

内置GSAP 3.15.0及MotionPathPlugin，版权头完整保留，许可证见 [GSAP标准许可证](https://gsap.com/standard-license) 和 `assets/vendor/LICENSE-URL.txt`。本技能是数据到旅行页面的构建器，没有可视化动画编辑器。

原生dialog抽屉的遮罩、打开关闭与进入动效参考 [Spectrum UI](https://github.com/arihantcodes/spectrum-ui) Animated Drawer。没有引入其React、Motion、Vaul或MCP运行时；Apache-2.0许可证见 `assets/vendor/SPECTRUM-LICENSE.txt`，也内嵌在输出说明里。

插画和模板是可修改源文件，不含原旅行参与者、酒店、定位、订单或聊天记录。示例明确为虚构。修改本地主题或插画不需要重新安装外部技能。
