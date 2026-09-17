# Roadtrip Storybook · 手绘旅行手账

把旅行 MD、文字安排或多份行程，做成带手绘地图、路线动画和翻页交互的离线 HTML。

![虚构示例预览](roadtrip-storybook/assets/preview.png)

## 可以做什么

- 手绘地图约占桌面页面的一半，停留点用路线连接。
- 汽车、步行、索道、火车和船使用各自的移动标记。
- 支持不同天数、人数、宠物、食宿、备选方案和行前清单。
- 支持键盘、按钮和手机滑动翻页，动效可关闭或暂停。
- 多份行程批量生成，成品自带脚本与资源，可离线打开。

这是可供 AI 代理调用的 **SKILL.md 技能及本地构建器**。模型负责理解资料、整理结构化输入；构建器不会靠关键词猜测任意 MD 的含义。仓库不是在线预订服务，也不提供实时导航或 HTTP API。

## 安装给 AI 使用

在支持 GitHub 技能安装的代理中，发送：

```text
请从 https://github.com/qrt345/roadtrip-storybook/tree/main/roadtrip-storybook
安装 roadtrip-storybook 技能。
```

也可下载本仓库 ZIP，将其中的 `roadtrip-storybook` 文件夹放入代理的个人技能目录。Codex 默认为 `~/.codex/skills/roadtrip-storybook`，设置了 `CODEX_HOME` 时使用其 `skills` 子目录。保持文件夹结构；不要直接覆盖自己修改过的同名技能。

安装后使用：

```text
使用 $roadtrip-storybook，把我提供的旅行 MD 做成手绘地图翻页 HTML。
保留已确认与待确认安排，小车沿路线移动，输出可离线打开的文件。
```

批量使用：

```text
使用 $roadtrip-storybook，读取这几份行程，为每份分别生成同风格 HTML。
人数、日期、交通、宠物及页数以各自资料为准，统一放入指定输出目录。
```

## 不依赖代理，直接试运行

需要 Python 3.9+，构建只使用标准库，无需 npm、API 密钥或在线服务。

```bash
git clone https://github.com/qrt345/roadtrip-storybook.git
cd roadtrip-storybook
python roadtrip-storybook/scripts/build.py --batch roadtrip-storybook/assets/examples --out-dir output
```

打开 `output/coast-weekend.html` 或 `output/mountain-rail.html`。示例全部为虚构，不能直接作为出游推荐。

准备自己的 JSON 后：

```bash
python roadtrip-storybook/scripts/build.py --input trip.json --output trip.html
python roadtrip-storybook/scripts/build.py --batch inputs --out-dir output
```

默认不覆盖已有文件，确认要更新时添加 `--force`；`--check` 只验证数据。整个批次先预检，结构错误时不开始生成。清单状态只存在读者自己的浏览器里，不会上传。

## 文档与验证

- [技能入口](roadtrip-storybook/SKILL.md)
- [输入数据格式](roadtrip-storybook/references/data-format.md)
- [完整使用说明](roadtrip-storybook/references/usage.md)

```bash
python -B tests/test_build.py
```

自动化浏览器检查需要另备 Python Playwright 和浏览器：

```bash
python roadtrip-storybook/scripts/verify.py --html output/coast-weekend.html --out-dir verification
```

已有系统 Edge 可加 `--channel msedge`，已有 Chrome 可加 `--channel chrome`。

## 资料、隐私与许可

“确定参加”“已预订”“准入已核实”和“参考价格”分别记录。页面不会把未经核实的安排升级为已落实；新增时效信息需要查询来源。分享前检查整份 JSON 和附带 MD，去除不应公开的精确住址、电话、订单与凭证。

地图是行程示意，方位、道路和比例不是导航数据。仓库包含的预览与示例均为虚构，不含作者私人旅行资料。

自有代码与文档使用 [MIT License](LICENSE)。内置 GSAP 与第三方材料保留各自许可证，见 [第三方说明](THIRD_PARTY_NOTICES.md)，不统一改授 MIT。
