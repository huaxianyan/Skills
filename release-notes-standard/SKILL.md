---
name: release-notes-standard
description: GitHub Release 发布说明与页面的统一规范。新功能与问题修复分开描述，让读者一眼看出哪些是新东西、哪些是旧缺陷被修；安装包按项目名、架构与版本号命名，并带上构建信息表。写发布说明、建 Release、给发布流程加门禁、把历史 Release 追溯回现行标准、给安装包命名时使用。触发语句：「发布 release」「发新版」「写发布说明」「Release 描述改一下」「把之前的 release 也按标准重写」「Release 标题只留版本号」「release 页面全是一样的看不出是哪个版本」「新功能和修复混在一起」「用户看不出哪些是新的」「apk 命名」「release 里就一个 apk」「产物名字看不出是什么」。
---

# 发布说明与 Release 页面规范

GitHub Release 页面是发布出去的门面。这里定一套跨项目通用的写法，配上可执行的门禁脚本。

目标：一屏读完知道这版改了什么，新功能与问题修复各是哪几条。详细内容留在仓库文档里。Release 列表能直接看出是哪个版本，下载下来的包一看名字就知道是什么。

## 格式门禁

脚本按下面的规则判。任何一条不过，CI 就该失败。

| 规则 | 判据 |
| --- | --- |
| 不得以一级标题开头 | 首行不能匹配 `# `。产品名和版本号由 Release 页面自己展示 |
| 行数 | 全文不超过 40 行 |
| 新功能与修复必须分开 | 至少出现 `## 新功能` 与 `## 问题修复` 中的一节，每个分类节必须有更新列表条目 |
| 必须链接详细记录 | 至少一条链接匹配 `/blob/v<标签>/`，指向该标签下真实存在的文档 |
| 禁止出现的节 | `## 使用说明`、`## 真机验收`、`## 构建与兼容范围`、`## 兼容边界` |
| 身份节至多一个 | `## 版本信息` 与 `## 构建信息` 只能出现一个，且通常由工作流追加 |

四个禁用节的原因一样：使用方式、验收过程、构建范围属于长期文档，写在 `docs/` 里可以随版本更新，
写在 Release 里就会在下一个版本变成过时的死文本。

### 为什么要分开

新功能与问题修复混在一节里，读者得逐条读完才知道哪些是新东西、哪些是原有缺陷被修掉了。
分节之后可以直接看到新增能力和已修复的问题，读者据此判断哪些变化与自己的使用场景有关。

## 标准形态

按本版实际包含的内容选一种。两节齐全时，新功能在前。

**两节齐全：**

```
<概述段：这版加了什么、修了什么，一到两句>

## 新功能

- **小标题**：说明

## 问题修复

- **小标题**：说明

<可选说明段：设计取舍、已知边界、升级注意事项>

完整实现与验收记录见 [标题](https://github.com/<owner>/<repo>/blob/v<版本>/<文档>)。

<许可证尾句>
```

**只有新功能：**

```
<概述段>

## 新功能

- **小标题**：说明
```

**只有问题修复：**

```
<概述段>

## 问题修复

- **小标题**：说明
```

几条写法上的要求：

- **概述段讲解决什么问题，不讲改了多少行。** 读者关心的是他的使用体验变了什么。
- **分节按改动性质，不按代码位置。** 一个新页面顺带修了一个崩溃，那就是两条，分别写进两节。
- **新功能写新增能力，问题修复写原有错误及修复结果。** 不把体验优化、内部重构或依赖升级硬归为 bug 修复。用户可感知的其他改进可另设 `## 改进`，内部实现细节留在详细记录里。
- **分类是否准确需要人工审阅。** 门禁只检查标题和条目结构，不判断改动是否属于新功能或旧缺陷。代码块里的示例不算分类节。
- **修完的旧缺陷要写清影响面**，让读者判断自己是否受影响。例如「空词典时会崩溃」比「修复崩溃」有用。
- **不要为了凑齐两节把新功能写成修复。** 只有修复的版本就只写修复，只有新功能的版本就只写新功能。
- **每一节内的每一条以加粗小标题开头**，冒号后写说明。一条说一件事。
- **链接的锚点要在那个标签下真实存在。** 核对方式：
  `git show <tag>:docs/architecture.md | grep -E '^#{1,3} '`。不要拿现在的文档结构去写历史版本的链接。
- **升级注意事项**（能否覆盖安装、要不要同步升级配套组件）放在最后一个更新节之后的说明段里。
- 说明文件只是 Release 正文的前半段，工作流会在后面追加 `## 构建信息`，所以自己不要写这一节。- **过渡期**：历史 Release 里的 `## 主要更新` 不强制回溯。存量版本可以保持原样，新版本按本节写法。

## 产物命名

Release 页面上只有 `release.apk` 或 `app-release.apk` 这类名字，读者无法确认它是哪个项目、哪个版本、哪种架构。下载到本地后更认不出来，存两个版本就会互相覆盖。

命名规则：

```text
<项目名>-<架构>-<版本号>.apk
<项目名>-<架构>-<版本号>.apk.sha256
```

例：`ComebackGooglePinyinInput-arm64-v8a-2.1.5.apk`。

- **只含 ASCII 字母、数字、`-` 和 `.`**。避开空格、中文和括号，它们在 URL、命令行与自动化工具里都要转义。
- **项目名用仓库名或产品名**，不用构建产物的默认名。
- **带架构**的包必须写清 ABI。多个 ABI 的产物不能重名。
- **版本号与 Release 标签一致**，不带 `v` 前缀，方便与文件名、目录名拼接。
- **校验文件用同名加 `.sha256` 后缀**，内容用 `sha256sum` 的默认格式 `SHA-256  <文件名>`。这样放同一目录即可直接 `sha256sum -c` 校验。

在发布步骤里用 `#` 语法重命名，不改构建产物，也不复制文件：

```bash
gh release create "$TAG" \
  "$APK_PATH#$RELEASE_APK_NAME" \
  "$APK_PATH.sha256#$RELEASE_APK_NAME.sha256" \
  --title "$TAG" --notes-file "$notes_out"
```

`#` 左边是实际文件路径，右边是上传后的资产名。这样构建输出保持默认名，只有 Release 上的名字统一。

上传后核一下资产名与预期一致：

```bash
gh release view "$TAG" --json assets -q '.assets[].name'
```

## Release 页面形态

- **标题就是标签本身**（`v0.2.0`），不加产品名前缀。
  加了前缀以后，左侧 Release 列表会变成一列被截断的同一个名字，看不出是哪个版本，
  反而失去了列表的作用。
- **正文 = 仓库里的发布说明文件 + 工作流追加的 `## 构建信息` 表**。
  构建信息表不能只放 SHA-256，要能回答「这个包是什么、能不能装、装了会替换什么」。

工作流里的拼装方式（`cat` 加 `printf` 直出，不要用模板引擎）。构建信息表按项目实际能力取字段，至少要能让读者确认包的来源、版本、适用设备与签名身份：

```bash
notes_out="build/release/release-notes.md"
mkdir -p "$(dirname "$notes_out")"
{
  cat "$notes_file"
  printf '\n## 构建信息\n\n'
  printf '| 项目 | 值 |\n'
  printf '| --- | --- |\n'
  printf '| 版本 | `%s` |\n' "$GITHUB_REF_NAME"
  printf '| 版本号 | `%s` |\n' "$VERSION_CODE"
  printf '| 架构 | `%s` |\n' "$ABI"
  printf '| min / target SDK | `%s / %s` |\n' "$MIN_SDK" "$TARGET_SDK"
  printf '| 包名 | `%s` |\n' "$APPLICATION_ID"
  printf '| 签名证书 SHA-256 | `%s` |\n' "$CERT_SHA256"
  printf '| 源码提交 | `%s` |\n' "$GITHUB_SHA"
  for apk in dist/*.apk; do
    printf '| %s SHA-256 | `%s` |\n' "${apk##*/}" "$(sha256sum "$apk" | cut -d' ' -f1)"
  done
} > "$notes_out"
```

字段选择：

| 字段 | 作用 |
| --- | --- |
| 版本、版本号 | 对应标签与安装包内部版本，确认升对了 |
| 架构 | 确认设备能不能装 |
| min / target SDK | 确认系统版本要求与行为变更基线 |
| 包名 | 确认会不会与已有应用共存或互相替换 |
| 签名证书 SHA-256 | 决定老用户能否覆盖安装。与上一版不一致就说明不能 |
| 源码提交 | 出问题时能定位到确切代码 |
| 产物 SHA-256 | 校验下载完整 |

签名证书与源码提交这两项不能省：前者决定能否覆盖升级，后者决定能不能复现。

```bash
notes_out="build/release/release-notes.md"
mkdir -p "$(dirname "$notes_out")"
{
  cat "$notes_file"
  printf '\n## 构建信息\n\n'
  printf '| 项目 | 值 |\n'
  printf '| --- | --- |\n'
  printf '| 版本 | `%s` |\n' "$GITHUB_REF_NAME"
  for apk in app/build/outputs/apk/release/app-release.apk \
             system-extension/build/outputs/apk/release/system-extension-release.apk; do
    printf '| %s SHA-256 | `%s` |\n' "${apk##*/}" "$(sha256sum "$apk" | cut -d' ' -f1)"
  done
} > "$notes_out"
gh release create "$GITHUB_REF_NAME" --title "$GITHUB_REF_NAME" --notes-file "$notes_out" ...
```

同时改已有的 Release 时只传 `--title`，正文不动。只传 `--notes-file`，标题不动。

```bash
gh release edit vX.Y.Z --title "vX.Y.Z" --notes-file /path/to/body.md
```

## 门禁脚本

```bash
python scripts/verify_release_notes.py docs/release-notes/v0.2.0.md
python scripts/verify_release_notes.py --tag v0.2.0
python scripts/verify_release_notes.py --tag v0.2.0 --dir docs/releases
```

参数：

- `notes`：要检查的文件，可以给多个。都不给时用 `--tag` 和 `--dir` 拼路径。
- `--tag`：版本标签，例如 `v0.2.0`。
- `--dir`：发布说明目录，默认 `docs/release-notes`。
- `--max-lines`：行数上限，默认 40。
- `--feature-heading`：追加新功能节名，可重复。默认含 `## 新功能`、`## 新特性`、`## 新增功能`。
- `--fix-heading`：追加问题修复节名，可重复。默认含 `## 问题修复`、`## 修复`、`## Bug 修复`、`## 缺陷修复`。
  英文项目用这两个参数追加自己的节名，例如 `--feature-heading '## Features' --fix-heading '## Bug Fixes'`。
- `--link-pattern`：详细记录链接的正则，默认 `/blob/v[^/\s]+/`。
  用 CHANGELOG 风格的项目改成 `CHANGELOG\.md#\d`。
- `--forbidden`：追加禁止出现的节，可以重复给。

`--summary-heading` 已移除。项目更新脚本时，应同时更新 CI 参数和新版本发布说明，不用旧的合并节名绕过分类要求。

通过时输出 `verified across N file(s)`，失败时逐条打印原因并以非零码退出。

修改门禁后运行回归测试：`python scripts/test_verify_release_notes.py`。测试覆盖分类节、空节、代码块示例和自定义节名，临时文件自动清理。

## 接到 CI

在打标签时才跑，放在发布步骤之前：

```yaml
      - name: Verify release notes
        if: startsWith(github.ref, 'refs/tags/v')
        run: python3 scripts/verify_release_notes.py --tag "$GITHUB_REF_NAME"
```

发布任务用 `if: startsWith(github.ref, 'refs/tags/v')` 控制，这样推分支只跑构建，推标签才发 Release。

## 发布顺序

1. **先在本地过门禁**，这一步不通后面全白做。
2. 提交并推主分支，等 CI 绿。这一步失败还有机会修。
3. 打注解标签并推送，触发发布。
4. 复核线上产物。

**发布成功后标签与 Release 都不可撤销。** 要重发得先删标签，修完再重打。
但 `gh release edit` 可以随时改标题与正文，不必删标签。

先推主分支再推标签的理由很简单：主分支那次失败可以重来，标签推出去就不能收回了。

## 复核线上产物

先看资产清单，再逐个下载核算。

```bash
gh release view vX.Y.Z --json tagName,name,assets \
  --template '{{.tagName}} | {{.name}}{{"\n"}}{{range .assets}}ASSET {{.name}}  {{.size}} bytes{{"\n"}}{{end}}'
```

逐项核对：

- 每个资产的大小与 `gh release view --json assets` 报的一致。
- 资产名符合上面的产物命名规则：项目名、架构、版本号齐全，只有 ASCII 字符。
- 正文的 `## 构建信息` 表里，架构、min / target SDK、包名、签名证书都与实际包一致。
- 下载后实测 SHA-256 与 `SHA256SUMS` 逐字节一致。
- 签名证书与上一版一致。**不一致就停下来问**，因为这决定老用户能否覆盖安装。
- 包的版本号是新的，且不含 debug 标志。
- 正文行数与结构符合上面的形态，链接的锚点真实存在。

直连 GitHub 慢的机器走代理下载：

```bash
curl -sS -L -o app-release.apk \
  "https://github.com/<owner>/<repo>/releases/download/vX.Y.Z/app-release.apk"
```

## 把标准追溯回历史 Release

门禁改了以后，历史 Release 不会自动更新。回填流程见
[references/retrofit-history.md](references/retrofit-history.md)，关键点有三条：

- 先备份旧正文，那是唯一的回滚手段。
- 不要拿仓库文件当历史事实，发布之后说明文件还可能改过，线上正文才是当时发出去的东西。
- 改完逐个复核，**确认资产数量和字节数没有变化**。改描述不该动产物。

## 项目适配清单

接手一个新项目时，先确认这几项，写进项目的 `AGENTS.md`：

- 版本号的唯一来源（例如 `gradle.properties`、`package.json`、`Cargo.toml`）。
- 发布说明目录。默认 `docs/release-notes/v<版本>.md`。
- **产物命名格式**：项目名、架构与版本号具体怎么拼，写进项目约定文件。
- **构建信息表要能填出哪些字段**：版本、架构、min / target SDK、包名、签名证书、源码提交。拿不到的字段要么补上取值来源，要么在项目约定文件里写明为何不需要。
- 详细记录的链接形态。多数项目用 `/blob/v<标签>/<文档>`，用 CHANGELOG 的项目改成 `CHANGELOG.md#<版本>`。
- 构建信息表要列哪些产物。
- 构建与签名的命令、签名证书指纹。
- CI 工作流的位置，以及 `release` 任务是不是只在标签下触发。

## 来源

这套规范在两个项目上跑通，门禁脚本从其中一个带发布流程的项目移植。产物命名与构建信息字段取自该项目一个 Android 应用的实践。
