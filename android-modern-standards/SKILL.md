---
name: android-modern-standards
description: Android 现代开发规范。目标 SDK 跟进最新稳定版、平台新特性尽量接入（预测性返回、edge-to-edge、大屏可调整性）、界面优先用原生 Material You 组件、动效参照指定的开源样板应用。新建或改造 Android 项目、提升 targetSdk、处理系统栏与返回手势、选界面组件、调转场动画时使用。触发语句：「升 targetSdk」「接入预测性返回」「支持 edge-to-edge」「Material You」「M3 Expressive」「这个转场不对」「动画不一致」「大屏适配」。
---

# Android 现代开发规范

三条主线：平台新特性尽量接入、界面走原生 Material、动效参照项目指定的样板应用。

版本相关的数字都标了核对日期。Android 一年一个大版本，数字会过时，判据和做法比较稳定。动手前先按文中的链接核对当前版本。

## 总则

- **目标 SDK 跟进最新稳定版**，不长期停在旧值。行为变更只在提升 `targetSdk` 后生效，停在旧值等于把兼容负担一直背下去。
- **新特性「尽量接入」的边界**：公开稳定 API 直接接入。实验性 API 可以先试，但要标注用途、隔离在可回退的分支，不当作长期基线。
- **不靠记忆判断「什么是新的」**。写代码前核对官方的行为变更清单，链接见下文各节。
- **能跑通的旧做法不等于还要继续用**。平台已经替你做了的事，不要自己再实现一套。

## 目标 SDK 与行为变更

### 每次提升前核对三份清单

1. 该版本**所有应用**都会受影响的行为变更。
2. 该版本 **`targetSdk` 达到该值**才会生效的行为变更。
3. 自己用到的 API 是否被废弃、收紧或改为默认开启。

官方入口：[行为变更总览](https://developer.android.com/about/versions)。按版本看 `behavior-changes-all` 与 `behavior-changes-<版本号>` 两篇。

### 版本节奏

- 每年一个大版本，春季开发者预览与 Beta，年中正式发布。
- QPR（季度平台版本）会加特性，不只是修 bug。Material 3 Expressive 就是随 Android 16 QPR1 铺开的。
- 截至 2026-10，Android 17（API 37）已正式发布，Android 16（API 36）是上一版。

## Edge-to-Edge

### 为什么必须做

- API 35（`targetSdk` 35）起强制 edge-to-edge，系统栏变透明。
- API 36 起**退出开关被废弃并禁用**，`windowOptOutEdgeToEdgeEnforcement` 不再起作用。
- 不做的话内容会被系统栏遮住，不是样式问题而是功能问题。

依据：[Android 16 行为变更](https://developer.android.com/about/versions/16/behavior-changes-16)。

### 接入方式

- Activity 的 `onCreate` 里调 `enableEdgeToEdge()`。它会把低版本也一并处理，放在 `setContent` 之前。
- 处理窗口 insets。用 `WindowInsets` 系列 API 或 Compose 的 `Modifier.windowInsetsPadding`。
- 可滚动内容要能延伸到系统栏下面，滚动时再通过 insets 让出空间。
- 输入法场景在 Manifest 设 `android:windowSoftInputMode="adjustResize"`。
- 三键导航栏默认带半透明遮罩，手势导航栏透明。需要去掉遮罩时用 `setNavigationBarContrastEnforced(false)`。

### 常见错误

- 只把状态栏设成透明，不处理 insets，结果内容被遮住。
- 整个布局用 `fitsSystemWindows` 一裹了事。这样确实不遮了，但也失去了 edge-to-edge 的意义。
- 硬编码状态栏高度。刘海、挖孔、折叠屏都不一样。
- 浅色深色主题下忘了切系统栏图标颜色。

## 预测性返回

### API 36 起的默认行为

`targetSdk` 达到 36 且设备为 API 36 以上时：

- 返回桌面、切换任务、切换 Activity 的系统动画**默认开启**。
- **`onBackPressed()` 不再被调用**，`KEYCODE_BACK` 也不再分发。

第二条是硬中断。还在用旧回调的应用会直接失去返回功能，必须迁移。

依据：[预测性返回接入指南](https://developer.android.com/guide/navigation/custom-back/predictive-back-gesture)。

### 迁移路径

- **Compose**：用 `PredictiveBackHandler`，来自 `androidx.activity` 1.6.0 以上。
- **View**：用 `OnBackPressedCallback`，或平台的 `OnBackInvokedCallback`。
- **不拦截返回的 Activity**：只需要系统动画时，在 Manifest 给它加 `android:enableOnBackInvokedCallback="true"`。
- 低版本兼容由 AndroidX 处理，不需要自己分支。

### 手势进度驱动的转场

要跟手预览，不是只做「提交后换页」：

- 用 `SeekableTransitionState` 配合 `Transition.AnimatedContent`，呈现真实的上一页。
- **不要在进度寻址的分支里复用交叉淡化**。手势停在中段时，旧页已淡出、新页还没显现，两页都很淡。这是最常见的返工点。
- 拖动只驱动呈现。提交后才更新返回栈，取消时恢复原页。
- 协程已取消时不要在异常分支里另起恢复动画。
- 用一个状态区分「手势中／收尾／空闲」，否则取消后会过早恢复普通动画效果。

### 迁移名单只留一个定义点

Manifest 里接入的 Activity 名单，与成品门禁脚本的检查清单，必须是同一份定义。维护两份必然会漂移，一处改了另一处忘。

## 界面：原生 Material 优先

### 判据

- **先用 Material 3 官方组件，再考虑自绘**。动手画之前先回答：官方组件为什么不够用。答不上来就用官方的。
- 动态取色（Material You）默认开启，跟随壁纸与系统深浅色，不要写死品牌色。
- 深浅色两套都要过一遍，不能只测一种。
- 无障碍标签、触摸目标尺寸、对比度是组件自带的能力，自绘会一并丢掉。

### Material 3 Expressive

- 稳定版查 [compose material3 release notes](https://developer.android.com/jetpack/androidx/releases/compose-material3)。截至 2026-10，稳定线为 `1.4.0`，`1.5.0-beta01` 已发布。
- `1.4.0` 内部已含 Expressive 的部分实现，但 `MaterialExpressiveTheme` 当时仍是 `internal`，不能当公开 API 调。
- Beta 线已公开 `MaterialExpressiveTheme`、`MotionScheme.expressive()`、`ButtonGroup`、`MediumFlexibleTopAppBar` 等。
- 其中一部分仍标 `@ExperimentalMaterial3ExpressiveApi`，Alpha 期间 API 与默认值仍会变。**不要把 alpha 当长期基线**，可以在隔离分支做原型。
- **内部 API 不得用反射、可见性抑制或自绘控件绕过**。编译不过就说明它不是公开接口，绕过等于把一个随时会变的内部实现绑进自己的代码。等它进 RC 再做正式接入。
- 官方资料：[Material 3 in Compose](https://developer.android.com/develop/ui/compose/designsystems/material3)、[M3 Expressive](https://m3.material.io/blog/building-with-m3-expressive)。

### 响应式与大屏

- 用 `material3-adaptive` 的 `WindowSizeClass` 与 `PaneScaffold` 做自适应，不按屏幕像素判断。
- **API 37 起对 `sw600dp` 以上的设备强制可调整**。系统会忽略 `screenOrientation`、`resizeableActivity=false`、`setRequestedOrientation()` 与宽高比限制。

依据：[Android 17 发布说明](https://developer.android.com/blog/posts/android-17-is-here)。

## 动效与转场

### 参照物

- **以项目指定的样板应用为准**，不看第三方模仿品。参照物由项目约定，没指定就先问，不要自己选一个。
- 本项目当前指定的参照是 `Pixel-Tailor-CN/PixelText`，其 [页面导航](https://github.com/Pixel-Tailor-CN/PixelText/blob/main/app/src/main/java/vip/mystery0/pixel/text/ui/AppNavigation.kt) 与 [主题](https://github.com/Pixel-Tailor-CN/PixelText/blob/main/app/src/main/java/vip/mystery0/pixel/text/ui/theme/Theme.kt) 是动效与主题的公开参考。
- **参照源码，不只凭观感**。把观感差异定位到具体参数，否则会调成「有点像」。
- **参照物是源码，不是依赖版本**。它的 `libs.versions.toml` 是另一回事，照搬版本号会把一堆预发布依赖一并引进来。看它怎么组织转场，不看它用什么版本。
- 与参照物对照时，同一场景在同一台设备上比，不拿不同设备或不同 Launcher 的表现互相推断。参照应用正常而自己不正常，说明差距在自己这侧。
- 核对自己看到的版本。公开主线可能已经领先于目标设备上安装的版本，不能把公开主线当作已安装版本的精确实现。

### 共享元素

- `SharedTransitionLayout` 包住最外层，内部用 `Modifier.sharedElement()` 或 `Modifier.sharedBounds()` 标记。
- 与 `AnimatedContent`、`AnimatedVisibility`、`NavHost` 结合使用，让它们管理过渡。
- 图片共享给相同的 cache key，否则会闪一下再替换。

依据：[Compose 共享元素](https://developer.android.com/develop/ui/compose/animation/shared-elements)。

### 不透明优先

手势与转场路径上优先用不透明滑动与分层位移，不要叠加透明度。透明度动画在进度被停住时最容易暴露问题。

前景完整位移、背景短距离位移、加轻微缩放与缓动，是参照物常用的组合。进入淡化较快、退出淡化延后，能避免手势中段两页同时发白。

### 分清 spatial 与 effects

M3 Expressive 把动效分成两类，命名与参数都按官方来，不要自创：

- **spatial**：位置、尺寸、圆角这类形状变化。
- **effects**：透明度、缩放这类不改变布局的效果。

两类各有 fast、default、slow 三档速度。Expressive 已把旧的「缓动加时长」换成弹簧物理参数，官方预设即 `MotionScheme.expressive()` 与 `standard()`。

依据：[Motion 概览](https://m3.material.io/styles/motion/overview/how-it-works)。

### 统一动效时先分清层次

- 不同层级的返回优先级不同：弹窗与底部面板要先于页面消费返回，否则会连页面一起退掉。
- 保存、取消、返回栈与首次引导退出的语义保持不变。换动画不是改业务契约的理由。
- 一次只统一一个范围，把不动的部分（如键盘、候选、手写等原生链）明确列出来。

### 帧率

- 需要高刷时请求系统公开的 `HIGH` 类别，结束后恢复 `NO_PREFERENCE`，**不固定具体 Hz**。
- 请求由整个动画的所有者统一管理，覆盖完整时长，不要在每个子元素上各请求一次。
- 不用改插值或缩短时长来掩盖调度问题。先分清是低频调度、真正掉帧，还是时序造成的观感停顿。

## 验证方式

- **静态门禁**：检查 `targetSdk`、退出开关是否缺席、接入 Activity 名单。名单与 Manifest 共用一处定义。
- **转场与返回逻辑**：写回归用例，用例依据真实报告过的缺陷，不凭想象补充。
- **真机对照**：优先在参照设备上跑参考应用，记录几何与时序。不靠截图下结论。
- **分层结论**：一条路径通过不等于全部场景通过。多层级、对话框、RTL、快速重复操作、生命周期中断都要单独验。
- **旧版本回归**：低 API 的 ART 行为与高版本不同，不能只在高版本测。

## 与项目约定文件的关系

- 具体版本号、依赖坐标、设备与调试信息写进项目的 `AGENTS.md` 或构建文件，不写死在本规范里。
- 本规范给判据与做法。涉及具体版本时以官方 release notes 为准，并把核对日期带上。
- 项目已定下的技术选型优先于本规范的一般建议，冲突时以项目约定为准。

## 来源

- 平台行为变更、edge-to-edge、预测性返回、共享元素、Material 3 的 API 与版本号均来自 [Android Developers 官方文档](https://developer.android.com/)，2026-10-11 核对。
- 动效参照物为 [Pixel-Tailor-CN/PixelText](https://github.com/Pixel-Tailor-CN/PixelText)，具体参考其页面导航与主题实现。
- 预测性返回的手势进度转场、不透明分层、迁移名单单一定义点等做法，来自一个真实 Android 项目在 API 36 上的三轮返工记录。
- 帧率请求 HIGH 类别、动画所有者统一管理的做法，来自该项目对原生动画链的帧间隔实测。
- 参照物与依赖版本分开对待、不凭观感定位差异，来自该项目统一动效时的记录。
