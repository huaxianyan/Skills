# 新项目建档骨架

把本目录整个复制进新仓库根，再把占位符换成实际内容：

```bash
cp -r <skills>/project-conventions/references/new-project/. <新仓库>/
```

要改的只有四处：

1. 根目录 `AGENTS.md`：把 `AGENTS.md.tmpl` 改名为 `AGENTS.md` 再填仓库身份、本地路径、构建命令、写入边界，控制在 100 行内。后缀是 `.tmpl` 的原因：magpie 安装技能时会跳过名叫 `AGENTS.md` 的文件，直接叫这个名字装完就丢了。
2. `docs/STATUS.md`：填四个「当前主线」小节，没内容就写「未开始」。
3. `RELEASE.md`：填发布前置、版本号位置与产物命名。
4. `docs/research/.gitkeep` 这份可删，等真写了研究文档再建。

`docs/handoff/` 只在需要把工作交给另一个执行者时写，一次一个文件，命名 `YYYY-MM-DD.md`；`docs/archive/` 建好就空着，等 `STATUS.md` 超预算再往里切。

建完跑一次检查，确认骨架符合规范：

```bash
python <skills>/project-conventions/scripts/check_docs.py <新仓库>
```
