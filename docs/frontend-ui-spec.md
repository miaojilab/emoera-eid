# E时代 ID 身份认证系统 — 前端界面规格说明书（UI Specification）

> 用途：供 AI / 前端工程师按本规格一比一复刻现有界面。
> 复刻目标：像素级还原布局、配色、动效、交互状态与响应式行为。
> 说明：本系统为 Django 服务端渲染（SSR）架构，所有页面基于 Django 模板 + Bootstrap 5 + Font Awesome 6 + 原生 JavaScript。规格中的 `{{ }}` 为服务端模板变量，复刻时以等价的数据绑定方式实现。

---

## 1. 技术栈与外部依赖

| 类别 | 依赖 | 来源 | 版本 |
|---|---|---|---|
| CSS 框架 | Bootstrap | `https://cdn.bootcdn.net/ajax/libs/bootstrap/5.1.3/css/bootstrap.min.css` | 5.1.3 |
| 图标库 | Font Awesome | `https://cdn.bootcdn.net/ajax/libs/font-awesome/6.0.0/css/all.min.css`（base 页）/ `https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css`（部分子页） | 6.0.0 |
| 字体 | Inter（300/400/500/600/700） | `https://fonts.loli.net/css2?family=Inter:wght@300;400;500;600;700&display=swap` | - |
| JS 依赖 | Popper.js + Bootstrap Bundle | `https://cdn.jsdelivr.net/npm/@popperjs/core@2.10.2/dist/umd/popper.min.js` + `https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.min.js` | 2.10.2 / 5.1.3 |
| 弹窗 | SweetAlert2 | `https://cdn.jsdelivr.net/npm/sweetalert2@11`（仅社团审核页） | 11 |
| 渲染 | Django 模板引擎 + `{% static %}` | 本地 | - |
| 语言 | `lang="zh"` | - | - |

> ⚠️ 注意：`base.html` 引用了 `{% static 'css/loading-styles.css' %}` 与 `{% static 'js/loading-manager.js' %}`（全局 Loading 管理器，通过 `window.loadingManager.showLoading(btn)` 调用）。当前仓库 `staticfiles/` 中**不存在**这两个文件，复刻时应自行实现等价能力：点击按钮后按钮进入 spinner 加载态（禁用 + `<span class="spinner-border spinner-border-sm me-2"></span>` 前缀文本），完成/失败后恢复；各页面 JS 均带有不依赖该管理器的手动 fallback。

---

## 2. 全局设计令牌（Design Tokens）

### 2.1 色板（定义于 base.html `:root`，全局 CSS 变量）

| 令牌 | 值 | 用途 |
|---|---|---|
| `--primary-color` | `#6366f1` | 主色·靛蓝（按钮渐变起点、进度条、激活态） |
| `--primary-dark` | `#4f46e5` | 主色深（按钮渐变终点） |
| `--secondary-color` | `#8b5cf6` | 次色·紫罗兰（导航栏渐变终点、图标底） |
| `--accent-color` | `#06b6d4` | 强调色·青色 |
| `--text-primary` | `#1f2937` | 正文主色（深灰） |
| `--text-secondary` | `#6b7280` | 正文次要色 |
| `--bg-light` | `#f9fafb` | 页面底色 |
| `--bg-white` | `#ffffff` | 卡片底色 |

**阴影令牌**：
- `--shadow-sm`: `0 1px 2px 0 rgb(0 0 0 / 0.05)`
- `--shadow-md`: `0 4px 6px -1px rgb(0 0 0 / 0.1)`
- `--shadow-lg`: `0 10px 15px -3px rgb(0 0 0 / 0.1)`

**常用渐变组合**（代码中反复出现，复刻必须保持一致）：
1. **品牌渐变**（导航栏、`btn-primary`、`btn-secondary`、图标圆底、进度条、卡片顶部装饰条）：
   `linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%)`
2. **页面头部渐变**（社团报名、申请状态、社团审核页的 card-header）：
   `linear-gradient(135deg, #667eea 0%, #764ba2 100%)`
3. **Hero 深色渐变**：`linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%)`
4. **技术区深色渐变**：`linear-gradient(135deg, #1e293b 0%, #334155 100%)`
5. **统计区浅灰渐变**：`linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%)`
6. **金色渐变**（强调文字/光晕）：`linear-gradient(45deg, #ffd700, #ffed4e, #ffd700)`；纯金 `#ffd700`
7. **管理端橙色变体**：`linear-gradient(135deg, #f59e0b, #d97706)`

**状态色**（沿用 Bootstrap）：success `#198754`、info `#0dcaf0`、warning `#ffc107`、danger `#dc3545`、成功绿渐变 `#2ecc71 → #27ae60`、错误红渐变 `#e74c3c → #c0392b`、加载灰渐变 `#bdc3c7 → #95a5a6`。

### 2.2 字体与排版

- 字体族：`font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif`
- 全局 `line-height: 1.6`；正文色 `var(--text-primary)`；页面底色 `var(--bg-light)`
- 标题字重：Hero 主标题 `800`、区块标题 `700`、卡片标题 `600`、导航品牌 `700`
- 所有元素 `box-sizing: border-box`；`* { margin:0; padding:0; }`

### 2.3 圆角与形状规范

| 元素 | 圆角 |
|---|---|
| 基础卡片 `.card` | `1rem`（16px），无边框，阴影 `--shadow-sm` |
| 大卡片（feature/stat/quick-action/function-card） | `1.5rem`（24px） |
| 业务页主卡片（社团报名/申请状态/审核） | `15px`（header 上方两角同为 15px） |
| 按钮 `.btn` | `0.5rem`（8px），无边框 |
| 徽章/胶囊（badge、section-badge、hero-badge、tech-badge） | `50px`（全胶囊） |
| 图标圆底 | 圆形（50%），直径 50/60/80/100/120px 不等 |
| Offer 主按钮 | `50px` 胶囊 |

### 2.4 间距节奏

- 页面区块（section）垂直 padding：主区块 `6rem`，次级区块 `5rem`，移动端 `3rem`
- 内容栅格间距：`row g-4`（即 gutter 1.5rem）
- 卡片内边距：常规 `2rem-2.5rem`，表单区 `p-4`
- 导航栏 padding：桌面 `1rem 0`，移动端 `0.75rem 0`
- `.main-content`：`min-height: calc(100vh - 80px); padding: 2rem 0`（首页为 `0`）

### 2.5 动效规范（关键帧全集）

| 动画 | 时长/缓动 | 效果 |
|---|---|---|
| `fadeIn` | 0.6s ease-in-out | 元素入场：`opacity 0→1; translateY(20px→0)`（类 `.fade-in`） |
| `slideInLeft` | 0.6s ease-out | `opacity 0→1; translateX(-30px→0)` |
| `slideInRight` | 0.6s ease-out | `opacity 0→1; translateX(30px→0)` |
| `float` | 6s ease-in-out infinite | `translateY(0→-20px); rotate(0deg→5deg)`（hero 主卡片与 4 个浮动元素，负延迟 -1s/-2s/-3s/-4s 错峰） |
| `gradient-shift` | 3s ease-in-out infinite | 渐变文字背景位移动画：`background-position 0% 50% → 100% 50%`（`background-size: 200% 200%`） |
| `pulse` | 2s ease-in-out infinite | 技术区同心环扩散：`translate(-50%,-50%) scale(0.8)→scale(1.2); opacity 1→0`，三个环延迟 0s/0.5s/1s |
| 卡片 hover | 0.3s~0.4s ease | `translateY(-4px ~ -12px)`（按卡片类型）+ 阴影升级至 `--shadow-lg`；feature-card 顶部 4px 渐变条 `scaleX(0→1)`；function-card 顶部 3px 渐变条展开 |
| 按钮 hover | 0.3s ease | `translateY(-1px ~ -2px)` + 阴影升级 |
| 进度条 | 宽度变化 `1s ease` | stat 进度条填充动画 |

---

## 3. 全局布局（base.html）

### 3.1 页面骨架

```
body（bg-light，Inter）
└── nav.navbar（品牌渐变，shadow-lg）
└── div.main-content（min-height calc(100vh-80px)）
    ├── div.container > messages（Bootstrap alert 列表）
    └── {% block content %}
└── script: Popper + Bootstrap JS + loading-manager.js
```

### 3.2 导航栏（全站唯一导航，除 Offer 确认页外所有页面继承）

- **容器**：`nav.navbar.navbar-expand-lg`，背景 `linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)`，`box-shadow: var(--shadow-lg)`，`padding: 1rem 0`
- **品牌区**（左）：
  - 图标 `<i class="fas fa-id-card-alt">` + 文本 `E时代 ID`（Bootstrap 类 `me-auto` 的 nav 列表置于其后）
  - 样式：`font-weight:700; font-size:1.5rem; color:white`，flex 居中，`gap:0.5rem`
  - hover：`color: rgba(255,255,255,0.9); transform: translateY(-1px)`
- **导航项**（`navbar-nav me-auto`，左对齐）：
  - 首页 `fa-home`、个人资料 `fa-user`、身份卡 `fa-id-card`、申请身份卡 `fa-shield-alt`、社团报名 `fa-users`
  - 审核身份卡 `fa-clipboard-check`（仅 `perms.members.can_review_applications` 可见）
  - 社团审核 `fa-user-check`（仅 `perms.members.can_review_club_applications` 可见）
  - 图标与文字间加 Bootstrap `me-1` 间距
  - 统一样式：`color: rgba(255,255,255,0.9); font-weight:500; padding:0.5rem 1rem; margin:0 0.25rem; border-radius:0.5rem`
  - hover：`color:white; background: rgba(255,255,255,0.1); translateY(-1px)`
  - **active 态**（按当前 URL name 匹配 `request.resolver_match.url_name`）：`background: rgba(255,255,255,0.2); color:white`
- **右侧栏**（`navbar-nav` 无 me-auto）：登录 `fa-sign-in-alt 登录` / 退出登录 `fa-sign-out-alt 退出登录`
- **移动端**：`navbar-toggler` 无边框、focus 无阴影，图标为白色三横线 SVG（`rgba(255,255,255,0.9)` 描边）

### 3.3 消息系统

- 位置：`.main-content` 内顶部 `.container`
- 结构：Bootstrap `.alert.alert-{{message.tags}}.alert-dismissible.fade.show`，前缀图标 `<i class="fas fa-info-circle me-2">`，右侧 `btn-close` 可关闭

### 3.4 全局卡片 / 按钮

- `.card`：无边框、圆角 1rem、`--shadow-sm`；hover 时 `translateY(-4px)` + `--shadow-lg`（子页面可覆盖）
- `.btn`：圆角 0.5rem、`font-weight:500`、`padding:0.75rem 1.5rem`、无边框、0.3s 过渡
- `.btn-primary`：`linear-gradient(135deg, #6366f1, #4f46e5)`；hover 上移 2px + `--shadow-md`
- `.btn-secondary`：`linear-gradient(135deg, #8b5cf6, #7c3aed)`；hover 同上
- `.btn-warning`（覆写）：`linear-gradient(135deg, #f59e0b, #d97706)`，白字，hover 加深

### 3.5 响应式基线（768px 断点）

- 导航 padding `0.75rem 0`，品牌 `1.25rem`
- `.main-content` padding `1rem 0`

---

## 4. 页面规格 — 首页 `index.html`

**布局性质**：单页垂直滚动营销页。`.main-content` 强制 `padding:0 !important`，内容紧贴导航栏。按顺序包含 6 个区块：

### 4.1 Hero 区（`.hero-section`）

- **背景**：品牌深色渐变（见 2.1-3），`min-height:100vh`，`display:flex; align-items:center`，`position:relative; overflow:hidden`，`padding:6rem 0`，白色文字
- **双层背景层**（绝对定位铺满，`z-index:1`）：
  1. `.hero-particles`：三层 radial-gradient 光斑 —— `rgba(120,119,198,0.3)` @ 20% 80%、`rgba(255,119,198,0.3)` @ 80% 20%、`rgba(120,219,255,0.2)` @ 40% 40%，均 `0%→transparent 50%`
  2. `.hero-grid`：50px×50px 网格线，`rgba(255,255,255,0.05)` 1px 横竖线
- **左列**（`col-lg-6 fade-in`，内容 `z-index:2`）自上而下：
  1. **胶囊徽章** `.hero-badge`：`rgba(255,255,255,0.1)` 底 + `backdrop-filter:blur(10px)` + 1px 白 0.2 边框 + 圆角 50px + `padding:0.75rem 1.5rem`，内为金色 `fa-star` + 文本 `内部身份认证系统`（0.875rem/500）
  2. **主标题** `.hero-title`：`4rem/800/line-height 1.1`，文本 `社团内部身份` + 内联 `<span class="text-gradient">认证</span>`（金色渐变文字 + `gradient-shift` 3s 无限动画，见 2.5）
  3. **副标题** `.hero-subtitle`：`1.25rem`、`opacity:0.9`、`line-height:1.7`，文案：`通过 E时代通行证 一键登录，快速完成身份认证，统一管理社团内部身份标识，参与活动报名等社团服务`
  4. **CTA 按钮组** `.hero-buttons`（`margin-bottom:3rem`）：
     - 登录态：`btn btn-primary btn-lg`「`fa-user-circle` 进入会员中心」+ `btn btn-outline-primary btn-lg`「`fa-id-card` 查看身份卡」
     - 未登录：`btn btn-primary btn-lg`「`fa-sign-in-alt` 一键登录」+ `btn btn-outline-primary btn-lg`「`fa-info-circle` 了解更多」链接至 `#features`
     - `.btn-outline-primary` 覆写：白字 + `2px rgba(255,255,255,0.3)` 边框 + 毛玻璃底；hover 时边框变纯白、底 `rgba(255,255,255,0.2)`、上移 2px
  5. **统计条** `.hero-stats`（flex，`gap:2rem`）：三项 `.stat-item` 居中——`100+ 活跃用户`、`99.9% 安全可靠`、`24/7 在线服务`；数字 `.stat-number` `1.5rem/700` 金色，标签 `.stat-label` `0.875rem` 白 0.9 透明
- **右列**（`col-lg-6 slide-in-right`）：`.hero-visual`（`height:500px`，flex 居中，`z-index:2`）
  - **主卡片** `.main-card`：200×280px，白 0.1→0.05 渐变 + `blur(20px)` 毛玻璃 + 1px 白 0.2 边框 + 圆角 20px，纵向居中排布：金色 `fa-id-card-alt` 3rem → 标题 `E时代 ID` 1.25rem → 说明 `您的数字身份凭证` 0.875rem/0.8 透明；`float` 6s 动画；外层 `.card-glow` 金色渐变模糊光晕（blur 10px、opacity 0.3、z-index -1）
  - **4 个浮动元素** `.floating-element`（80×80px 圆形，白 0.1 底 + blur 10px + 1px 白 0.2 边框，图标 1.5rem 白，`float` 动画错峰）：
    - `floating-1`（shield-alt）`top:10%; right:15%`，延迟 -1s
    - `floating-2`（users）`bottom:20%; right:5%`，延迟 -2s
    - `floating-3`（lock）`top:30%; left:10%`，延迟 -3s
    - `floating-4`（check-circle）`bottom:10%; left:20%`，延迟 -4s

### 4.2 功能特色区 `.features-section`

- 白底，`padding:6rem 0`
- **区块头**（居中，`mb-5`）：
  - `.section-badge`：品牌渐变底白字胶囊（`fa-rocket 核心功能`，圆角 50px，`padding:0.75rem 1.5rem`，`mb-1.5rem`）
  - `.section-title`：`3rem/700`，`为您提供全方位的数字身份服务`
  - `.section-subtitle`：`1.125rem` 次级色，`max-width:600px` 居中，`采用先进技术，确保安全可靠，让您的数字生活更加便捷`
- **卡片网格**：`row g-4`，四列 `col-md-6 col-lg-3 fade-in`：
  | 图标 | 标题 | 描述 |
  |---|---|---|
  | `fa-id-card` | 身份认证 | 快速验证身份信息，获取官方认证身份标识，享受专属权益 |
  | `fa-shield-alt` | 安全可靠 | 采用先进加密技术和多重安全验证，保护您的个人信息安全 |
  | `fa-users` | 社团活动 | 便捷参与各类社团活动，扩展社交网络，丰富校园生活 |
  | `fa-mobile-alt` | 移动便捷 | 随时随地访问，支持多设备同步使用，响应式设计完美适配 |
- `.feature-card`：白底、圆角 1.5rem、`--shadow-sm`、`height:100%`、`padding:3rem 2rem`、居中、1px 黑 0.05 边框；`:before` 顶部 4px 品牌渐变条 `scaleX(0)`；hover 时渐变条展开 + `translateY(-12px)` + `--shadow-lg`（0.4s）
- `.feature-icon`：100×100px 圆形，品牌渐变底白图标 `2.5rem`，居中 `mb-2rem`；`:after` 同渐变模糊光晕（blur 10px、opacity 0.3、z-index -1）

### 4.3 统计数据区 `.stats-section`（仅登录态渲染）

- 浅灰渐变背景（见 2.1-5），`padding:5rem 0`
- 三列 `col-md-4 fade-in`：
  | 图标 | 标题 | 标签 | 进度条宽度 |
  |---|---|---|---|
  | `fa-check-circle` | 认证完成 | 身份验证已通过 | 100% |
  | `fa-star` | 会员等级 | 享受专属权益 | 85% |
  | `fa-calendar-check` | 活动参与 | 参与各类活动 | 70% |
- `.stat-card`：白底、圆角 1.5rem、flex 居中、`padding:2.5rem`、1px 黑 0.05 边框；hover 上移 8px + `--shadow-lg`
- `.stat-icon`：80×80px 圆形，`linear-gradient(135deg, #06b6d4, #6366f1)` 底白图标 2rem，`margin-right:2rem`，不收缩
- 进度条：6px 高、底 `#e2e8f0` 圆角 3px，`.progress-bar` 品牌渐变填充，宽度变化 1s ease

### 4.4 快速操作区 `.quick-actions-section`（仅登录态渲染）

- 白底，`padding:5rem 0`；区块头样式同 4.2（badge `fa-bolt 快速操作`，标题 `常用功能一键直达`，副标题 `高效便捷的操作体验，让您的工作更加轻松`）
- 四列 `col-md-3 col-sm-6 fade-in` 链接卡片 `.quick-action-card`：
  | 图标 | 文本 | 目标 |
  |---|---|---|
  | `fa-shield-alt` | 申请认证 | /verify/ |
  | `fa-users` | 社团报名 | /club/ |
  | `fa-user-edit` | 编辑资料 | /profile/ |
  | `fa-id-card` | 身份卡 | /identity-card/ |
- 结构：纵向居中 flex，`padding:2.5rem 1.5rem`，圆角 1.5rem，`--shadow-sm`，1px 黑 0.05 边框，`text-decoration:none`，`height:100%`
- `.quick-action-icon`：80×80px 圆形，`linear-gradient(135deg, #8b5cf6, #06b6d4)` 底白图标 2rem，`mb-1.5rem`，带模糊光晕 `:after`
- hover：上移 8px + `--shadow-lg` + 文字变主题色；右上角 `.quick-action-hover`（`fa-arrow-right`，`top:1rem; right:1rem`）从 `translateX(-10px) opacity:0` 滑入显现

### 4.5 技术优势区 `.tech-advantages-section`

- 深蓝灰渐变背景（见 2.1-4），白字，`padding:6rem 0`；`row align-items-center`
- **左列**（`col-lg-6 fade-in`）：
  - `.tech-badge`：白 0.1 底毛玻璃胶囊（`fa-cog` 青色图标 + `技术优势`）
  - `.tech-title`：`2.5rem/700`，`先进技术保障`
  - `.tech-description`：`1.125rem`、`opacity:0.9`、`line-height:1.7`，文案：`采用最新的加密技术和安全协议，确保您的数据安全。支持多因素认证，实时监控异常行为，为您提供企业级的安全保障。`
  - `.tech-features`（纵向 gap 1rem）：三行 `fa-check text-success` + 文本 —— `端到端加密` / `多因素认证` / `实时安全监控`
- **右列**（`col-lg-6 slide-in-right`）：`.tech-visual`（`height:400px` flex 居中）
  - `.tech-card`（200×200px 相对定位）→ `.tech-icon`：120×120px 圆形，`linear-gradient(135deg, #06b6d4, #0891b2)` 底白 `fa-lock` 3rem
  - `.tech-rings` 三层同心环：`2px rgba(6,182,212,0.3)` 边框圆，直径 200/280/360px，`pulse` 2s 无限动画错峰（0s/0.5s/1s）

### 4.6 页脚 `.footer-info`

- `bg-light`，`padding:3rem 0`，`border-top:1px solid #e5e7eb`
- 居中一行：`fa-heart text-danger` + `E时代身份认证系统 - 让数字生活更美好`（text-muted）

### 4.7 首页响应式

- **≤768px**：hero-title `2.5rem`；hero-subtitle `1.125rem`；hero-buttons 内按钮 `display:block; width:100%; margin-bottom:1rem`（末个无下边距）；section-title `2rem`；hero-stats 纵向（gap 1rem）；hero-visual `height:300px; margin-top:2rem`；main-card 150×200px；floating-element 60×60px `1.25rem` 图标；tech-title `2rem`
- **≤576px**：hero-section padding `3rem 0`；四个 section padding `3rem 0`；stat-card 纵向居中（stat-icon `margin-right:0; margin-bottom:1.5rem`）

---

## 5. 页面规格 — 个人资料 `profile.html`

### 5.1 资料主卡片

- 栅格：`col-md-8 offset-md-2`
- `.card`：header 内 `h4 个人资料`；body 含：
  - 居中 120×120px 圆形头像 `{{ user_info.avatar }}`
  - 只读表单控件（`form-control` + `readonly`）：`用户名`、`邮箱`、`个人简介`（`textarea rows=3`）、`注册时间`
  - 底部居中按钮 `btn btn-primary`：`前往认证中心修改资料`，新窗口打开 `https://account.emoera.com/`

### 5.2 系统功能导航卡片（`mt-5` 全宽）

- header：`h4` 内 `fa-th-large` + `系统功能导航`；副标题 `text-muted mb-0`：`快速访问本站主要功能`
- body 网格 `row g-4`，单元 `col-md-6 col-lg-4`，共 6 个 `.function-card`：

| 卡片 | 图标 | 标题 | 描述 | 按钮 |
|---|---|---|---|---|
| 身份管理 | `fa-id-card` | 身份管理 | 查看和管理您的数字身份信息 | 查看身份卡（primary） |
| 身份认证 | `fa-shield-alt` | 身份认证 | 申请身份认证，提升会员等级 | 申请认证（primary） |
| 社团报名 | `fa-users` | 社团报名 | 加入E时代核心团队 | 加入E时代（primary） |
| 申请状态 | `fa-clipboard-list` | 申请状态 | 查看您的各种申请处理进度 | 查看状态（primary） |
| 审核申请（仅审核权限） | `fa-clipboard-check` | 审核申请 | 审核用户提交的身份认证申请 | 开始审核（warning） |
| 社团审核（仅社团审核权限） | `fa-user-check` | 社团审核 | 审核用户提交的社团报名申请 | 开始审核（warning） |

- `.function-card`：白底、1px 黑 0.1 边框、圆角 1rem、`padding:1.5rem`、`height:100%`；`:before` 顶部 3px 品牌渐变条 `scaleX(0)`；hover 渐变条展开 + `translateY(-4px)` + `--shadow-md` + 边框变 `--primary-color`
- `.function-card-admin`：顶部条与图标改为橙色渐变（`#f59e0b→#d97706`），hover 边框 `#f59e0b`
- `.function-icon`：60×60px 圆形渐变底白图标 1.5rem
- 按钮为 `.btn-sm`（覆写：`padding:0.5rem 1rem; font-size:0.875rem`）
- 移动端 ≤768px：卡片 `padding:1rem`；按钮纵向全宽

---

## 6. 页面规格 — 身份卡 `identity_card.html`

- **用户信息卡**（`card mb-4`）：左 80×80px 圆形头像（`object-fit:cover`）；右 `h3` 用户名 + `text-muted` 简介（缺省文案：`这个用户很懒，还没有填写简介`）
- **卡片网格**：`row`，单元 `col-md-6 col-lg-4 mb-4`：
  - 卡图：`img.img-fluid.w-100`，`max-height:200px; object-fit:contain`
  - 卡体：标题 `h5.card-title ps-5`；`identity_title`（`card-text text-muted ps-5`）；认证时间（`text-muted small ps-5`，格式 `Y-m-d H:i`，前缀 `认证时间：`）
  - hover：`translateY(-5px)` + `box-shadow: 0 10px 20px rgba(0,0,0,0.1)`（0.3s）
- **空状态**（无卡片时）：居中 `py-5`，`fa-card-text`（Bootstrap Icons class 写法，实际为 `bi bi-card-text display-1`）→ `暂无身份卡` → `您可以通过认证获取身份卡` → `btn btn-primary 申请认证`

---

## 7. 页面规格 — 申请认证 `verify.html`

- 栅格：`container py-5 > row justify-content-center > col-md-8 col-lg-6`
- 主卡片 `card shadow-sm`，body `p-4`：居中标题 `申请认证`
- **表单**（`needs-validation novalidate`，Bootstrap 原生校验，提交时 `form.classList.add('was-validated')`）：
  | 字段 | 控件 | 校验提示 |
  |---|---|---|
  | 姓名 | text | `请输入您的姓名` |
  | 学号 | text | `请输入您的学号` |
  | 认证身份 | text，placeholder `例：E时代23级核心成员` | form-text：`请填写您想要认证的具体身份，例如：E时代23级核心成员`；invalid：`请输入您要认证的身份` |
  | 身份类型 | select，占位项 `请选择身份类型`（disabled/selected） | `请选择身份类型` |
  - 提交按钮：`d-grid` 内 `btn btn-primary btn-lg 提交申请`
- **申请历史**（存在 `previous_applications` 时，`mt-4`）：标题 `h3.h5 申请历史`；逐条 `card mb-2`：左 身份标题 + `small.text-muted`（`类型 · 申请时间：Y-m-d H:i`），右状态 badge（success/danger/warning）

---

## 8. 页面规格 — 社团报名 `club_application.html`（三步向导）

- 栅格：`container-fluid > row justify-content-center > col-lg-8 col-md-10`

### 8.1 页面主卡片

- `card shadow-lg border-0 mb-4`，圆角 `15px`
- **header**：`#667eea→#764ba2` 渐变、白字、居中、`py-4`、上方两角圆角 15px；`h2`：`fa-users  E时代社团报名`；下方 `badge bg-light text-primary fs-6 新生加入申请`

### 8.2 分支状态

1. **已有申请**：`alert alert-info`（圆角 10px，左边框 4px `#0dcaf0`）——`fa-info-circle` + `您已提交申请` + `申请状态：{{status}}` + `申请时间：Y年m月d日 H:i` + 右侧 `查看申请状态` 按钮
2. **重新申请提示**（曾被拒）：`alert-info` 内 `重新申请` + `您之前的申请未通过审核（申请时间：…），现在可以重新提交申请。`
3. **正常流程**（下方三步）：

### 8.3 三步向导（`step-content` 切换）

- **顶部进度条**：6px 高 `progress` + `progress-bar bg-primary`（初始宽度 50%）；下方三个节点标签：`认证检查 / 信息填写 / 提交完成`（`small text-muted`）
- **Step 1 认证检查**：居中卡片——`fa-shield-alt fs-1 text-primary` + `第一步：认证状态检查` + `正在验证您的外部认证状态...`；`开始检查` 按钮（`btn btn-primary btn-lg px-4`，`fa-play`）；点击后按钮隐藏、显示 spinner 加载块；结果渲染进 `#verificationResult`（`alert` 各状态，见下）；**若无现有申请，页面加载 1 秒后自动触发检查**
  - 认证通过 → `alert-success`：`认证通过` + 状态文本 + `下一步` 按钮（`onclick="nextStep()"`）
  - 未提交（需注册） → `alert-warning`：`需要完成认证` + 引导链接 `https://trust.emoera.com/schemes/3` + `重新检查` 按钮
  - 审核中 → `alert-warning`：`认证审核中` + 状态 + `重新检查`
  - 404（未注册） → `alert-warning`：`需要注册并完成认证` + 链接 + 提示 `首次使用需要先注册认证系统账号` + `重新检查`
  - 失败 → `alert-danger`：`检查失败` + 错误信息 + `重新检查`
  - 网络错误 → `alert-danger`：`网络错误` + 重试提示 + `重新检查`
- **Step 2 信息确认**：`h4`：`fa-user-edit 第二步：个人信息确认`
  - `真实姓名`（必填，`form-control-lg`，placeholder `请输入您的真实姓名`，invalid-feedback `请填写真实姓名`，失焦清空 `is-invalid`）
  - `平台邮箱`（只读，值来自登录态邮箱）；`form-text`：`如果邮箱不正确，请到 https://account.emoera.com/profile 修改邮箱并退出重新登录此平台即可自动同步新邮箱`
  - 底部按钮行（`d-flex justify-content-between mt-4`）：`上一步`（`btn btn-outline-secondary`，`fa-arrow-left`）+ `提交申请`（`btn btn-success btn-lg px-4`，`fa-paper-plane`）
  - 提交：真实姓名为空则标红并 toast 警告；否则按钮进入 loading 态，POST `/club/submit/`（JSON：`real_name / external_status / external_verified`）
- **Step 3 提交完成**：居中——`fa-check-circle fs-1 text-success` + `h3.text-success 申请提交成功！` + `您的申请已成功提交，请等待审核。我们会通过邮件通知您审核结果。` + `btn btn-primary btn-lg 查看申请状态`

### 8.4 Toast 通知系统

- 容器：`position-fixed top-0 end-0 p-3`；`#notificationToast`：header 内 `fa-bell text-primary` + `通知` + 关闭按钮；body `#toastMessage`
- 类型切换（header 图标与颜色）：success `fa-check-circle text-success` / error `fa-times-circle text-danger` / warning `fa-exclamation-triangle text-warning` / info `fa-bell text-primary`
- 表单聚焦态：`border-color:#667eea; box-shadow: 0 0 0 0.2rem rgba(102,126,234,0.25)`

---

## 9. 页面规格 — 申请状态 `application_status.html`

- 栅格：`container-fluid > row justify-content-center > col-lg-10 col-md-12`

### 9.1 头部

- 渐变 header（同 8.1）：左 `h2`（`fa-clipboard-check 申请状态`），右**状态 badge**（`badge bg-light text-primary fs-6 status-badge`，圆角 20px、`padding:0.5rem 1rem`）：
  `待审核 / 笔试通知已发送 / 录取通知已发送 / Offer已确认 / 已拒绝`

### 9.2 基本信息网格（`row mb-4`，四格 `col-md-6`）

| 标签 | 值 |
|---|---|
| 申请人 | `{{real_name}}`（fw-bold） |
| 申请时间 | `Y年m月d日 H:i`（fw-bold） |
| 外部认证状态 | badge：`bg-success 已认证` / `bg-warning 未认证` |
| 最后更新 | `Y年m月d日 H:i`（fw-bold） |

- `.info-item`：`padding:0.5rem 0`；label `0.8rem/600/uppercase/letter-spacing 0.5px` 灰色

### 9.3 进度条（`mb-4`）

- `h5`：`fa-route 申请进度`；8px 高 progress + `progress-bar bg-primary`
- 宽度映射：pending 25% / interview_sent 50% / offer_sent 75% / offer_confirmed 100%（rejected 25%）
- 四节点标签（`small fw-bold`）：`提交申请 笔试通知 录取通知 完成`——已到达节点 `text-primary`，未到达 `text-muted`

### 9.4 状态详情（按状态分支，均为 `alert` 圆角 10px + 左边框 4px 状态色）

| 状态 | 视觉 | 文案 |
|---|---|---|
| pending | info | `fa-clock` + `等待审核` + `您的申请已提交成功，请耐心等待管理员审核。我们会尽快处理您的申请。` |
| interview_sent | success | `fa-check-circle` + `您已通过初筛` + `已向您的邮箱发送笔试通知，请查收。如有疑问，请联系管理员。` + `笔试通知发送时间：…` |
| offer_sent | success + 子卡片 | `fa-trophy text-warning` + `恭喜您被录取！` + `您已被录取，请检查邮箱及时确认offer。` + `录取通知发送时间：…`；下方子卡片（`bg-light` 圆角 10px）：`fa-handshake Offer确认状态` + `fa-clock text-warning 等待Offer确认` / `fa-check-circle text-success Offer已确认` + （未确认时）`btn btn-primary` 外链 `确认Offer` |
| offer_confirmed | 居中庆祝 | `fa-star fs-1 text-warning` + `h3.text-success 欢迎加入E时代！` + `您已成功确认offer并加入我们的团队。期待与您一起创造精彩！` + `Offer确认时间：…` |
| rejected | danger | `fa-times-circle` + `申请未通过` + `很遗憾，您的申请未通过审核。感谢您对E时代的关注，欢迎重新申请！` + `btn btn-outline-primary 重新申请` |

### 9.5 底部操作

- `d-flex justify-content-between mt-4`：`刷新状态`（`btn btn-outline-primary`，`fa-sync-alt`，reload）+ `返回`（`btn btn-secondary`，`fa-arrow-left`，非 rejected 时显示）
- ≤768px：该行纵向堆叠（gap 1rem），info-item 居中

---

## 10. 页面规格 — 认证申请审核 `review.html`（后台）

- 栅格：`container py-4`
- **头部行**（`d-flex justify-content-between align-items-center mb-4`）：`h2.h3 认证申请审核` + 状态筛选 `btn btn-outline-secondary dropdown-toggle`（下拉项：全部/待审核/已通过/已拒绝，`?status=` 参数，选中项 `dropdown-item active`）
- **表格**：`table table-hover align-middle` + `thead.table-light`，列：`申请人 / 姓名 / 学号 / 认证身份 / 身份类型 / 申请时间 / 状态 / 操作`
  - 申请人列：32×32px 圆形头像（若有）+ 用户名
  - 状态 badge：`bg-success`（approved）/ `bg-danger`（rejected）/ `bg-warning`（pending）
  - 操作组：`编辑`（`btn btn-sm btn-outline-primary`，触发 `#editModal{id}`）+ pending 时追加 `通过`（success）/ `拒绝`（danger）
- **编辑模态框**（每行一个 `modal fade`）：标题 `编辑申请信息`；表单字段 `姓名 / 学号 / 认证身份 / 身份类型`（select）；footer `取消`（btn-secondary）+ `保存更改`（btn-primary），POST 至 `/verify/edit/{id}/`
- **通过/拒绝交互**：原生 `confirm()` 确认 → fetch POST `/verify/approve/{id}/` 或 `/verify/reject/{id}/`（带 `X-CSRFToken`）→ 成功后 `location.reload()`

---

## 11. 页面规格 — 社团申请审核 `review_club_applications.html`（后台）

### 11.1 头部

- 渐变 header：左 `h2`（`fa-user-check 社团申请审核`）；右侧工具栏：状态 `select#statusFilter`（`form-select bg-white text-dark`，`width:auto`，六项：全部状态/待审核/笔试通知已发送/录取通知已发送/Offer已确认/已拒绝，切换即跳转 `?status=`）+ `刷新` 按钮（`btn btn-light`，`fa-sync-alt`）

### 11.2 统计卡行（`row mb-4`，六张 `col-md-2 col-sm-6 mb-3`）

`.stat-card`（`#f8f9fa` 底、1px `#e9ecef` 边框、圆角 10px、`padding:1rem`、居中；hover 上移 2px + 阴影）：

| 图标（50px 圆底） | 数值 | 标签 |
|---|---|---|
| `fa-clipboard-list` bg-primary | 总申请数 | 总申请数 |
| `fa-clock` bg-warning | 待审核 | 待审核 |
| `fa-envelope` bg-info | 笔试通知已发 | 笔试通知已发 |
| `fa-trophy` bg-success | 录取通知已发 | 录取通知已发 |
| `fa-handshake` bg-primary | 已确认 | 已确认 |
| `fa-times` bg-danger | 已拒绝 | 已拒绝 |

### 11.3 申请表格

- `table table-hover` + `thead.table-dark`，列：`ID / 姓名 / 用户名 / 邮箱 / 状态 / 外部认证 / 申请时间 / 操作（居中）`
- 状态 badge 色映射：pending→`bg-warning`、interview_sent→`bg-info`、offer_sent→`bg-success`、offer_confirmed→`bg-primary`、rejected→`bg-danger`
- 外部认证 badge：`bg-success 已认证` / `bg-warning 未认证`
- 申请时间格式 `m/d H:i`
- **操作列按状态**：
  - pending：`笔试通知`（btn-sm primary）+ `拒绝`（btn-sm danger）
  - interview_sent：`fa-redo 重发笔试`（btn-outline-info）+ `录取通知`（btn-sm success）+ `拒绝`（btn-sm danger）
  - offer_sent：`fa-redo 重发录取`（btn-outline-success）+ `查看Offer`（btn-sm info，外链 `/club/confirm-offer/{uuid}/`）
  - offer_confirmed：`已完成`（text-success）
  - rejected：`已拒绝`（text-muted）
- 空态：`td colspan=8 text-center text-muted py-4`，`fa-inbox fs-2` + `暂无申请记录`
- `.table-responsive` 圆角 10px + 外阴影 `0 0 20px rgba(0,0,0,0.1)`

### 11.4 操作交互（SweetAlert2）

| 动作 | 弹窗 | 确认后 |
|---|---|---|
| 笔试通知 | `question` 图标：`确定要向 {name} 发送笔试通知吗？` | POST `/club/admin/interview/{id}/` → 成功 Swal `发送笔试通知成功` → reload |
| 重发笔试 | `warning` 图标 + html 强调 + 注意文案 | POST `/club/admin/resend-interview/{id}/` |
| 录取通知 | `question`：`确定要向 {name} 发送录取通知吗？` | POST `/club/admin/offer/{id}/` |
| 重发录取 | `warning` | POST `/club/admin/resend-offer/{id}/` |
| 拒绝 | `warning`：`确定要拒绝 {name} 的申请吗？此操作不可撤销。` | POST `/club/admin/reject/{id}/` |

- 所有 fetch 均带 `X-CSRFToken`；失败/异常分别 Swal `失败/错误`

---

## 12. 页面规格 — Offer 确认 `confirm_offer.html`（独立全屏页，不继承 base）

### 12.1 页面骨架

- `lang="zh-CN"`；引用 Bootstrap **5.3.0**（jsdelivr）+ Font Awesome 6；独立 `<style>`（不依赖任何全局样式）

### 12.2 背景

- `body`：`min-height:100vh`、flex 居中、`font-family: Arial`、**四色流动渐变背景**：
  `linear-gradient(-45deg, #667eea, #764ba2, #f093fb, #f5576c)`，`background-size:400% 400%`，`gradientShift` 15s ease infinite（关键帧：背景位置 `0% 50% → 100% 50% → 0% 50%`）

### 12.3 Offer 成功容器 `.offer-container`

- `max-width:500px; width:90%`，`rgba(255,255,255,0.95)` 底 + `blur(10px)`、圆角 20px、`box-shadow: 0 20px 40px rgba(0,0,0,0.15)`、`padding:3rem`、居中、`position:relative; overflow:hidden`
- `::before` 顶部 5px 渐变条（`90deg #667eea→#764ba2`）
- 元素顺序：
  1. `.logo`：100×100px 圆形，背景图 `https://we.emoera.com/img/elogo.jpg`（cover），4px 白边框 + 阴影，hover `scale(1.1)`（0.3s）
  2. `h1`：`#2c3e50`、`2rem/700`：`您好，{{real_name}}！`
  3. `.offer-title`：`1.4rem/600 #667eea`：`fa-trophy text-warning 恭喜获得 E时代 核心团队 Offer`
  4. `.welcome-text`：`#7f8c8d`、`line-height:1.6`：`感谢您对E时代的关注与支持！我们的社团文化是开放包容，真诚热爱，欢迎您的加入。期待与您一同开启新的征程，互相支持，共同成长。`
  5. **主按钮状态机**（`.offer-btn`：`padding:1rem 2.5rem; font-size:1.2rem/600; 圆角50px; uppercase; letter-spacing:1px; min-width:200px`）：
     - 初始（未确认）：`loading-btn` 灰渐变 + spinner `加载中...`，禁用；**1.5s 后**切换为 `accept-btn`（`#667eea→#764ba2` 渐变、`fa-handshake 接受 Offer`），点击触发 `acceptOffer()`
     - 点击瞬间：按钮位置触发全屏**烟花爆发**；按钮变 `确认中...`（spinner + 禁用）
     - 成功：`accepted-btn` 绿渐变（`#2ecc71→#27ae60`，`fa-check-circle 已接受`），点击可重放烟花 + 提示 toast；随后 `location.reload()` 显示确认时间
     - 失败：`error-btn` 红渐变（`fa-times 确认失败` / `网络错误`）
  6. 已确认态：`accepted-btn 已接受` + `fa-calendar-alt 确认时间：Y年m月d日`
  7. 页脚小字：`fa-heart text-danger 再次感谢您的加入 - E时代研发中心`
- **错误容器** `.error-container`（error 时）：400px 宽毛玻璃白卡，`fa-exclamation-triangle error-icon`（4rem 红色）+ `h2.text-danger 出现错误` + 错误信息 + `btn btn-outline-primary 返回`（`window.close()`）

### 12.4 Toast 系统

- 容器 `position-fixed top:20px right:20px z-index:1050 max-width:350px`
- `.toast-custom`：毛玻璃白底、圆角 15px、`box-shadow: 0 10px 30px rgba(0,0,0,0.15)`；header 按类型渐变：info `#667eea→#764ba2`、success `#2ecc71→#27ae60`、error `#e74c3c→#c0392b`（白字、白关闭按钮）；自动隐藏 4s

### 12.5 烟花 Canvas 系统（`#confettiCanvas`，`position:fixed` 全屏 `pointer-events:none` `z-index:1000`）

- 每次爆发：150 个常规粒子（10 色：`#667eea #764ba2 #f093fb #f5576c #FFD700 #FF6B6B #4ecdc4 #45b7d1 #ff9a9e #fecfef`）+ 30 个星形大粒子
- 物理：初速（径向 4-12）+ 重力 `vy += 0.1` + 旋转 + `life` 衰减（0.002~0.017）；粒子形状：圆形/方形（30%）/星形（仅大颗粒）
- 渲染循环：`requestAnimationFrame`，粒子耗尽后隐藏画布；resize 时重建画布尺寸
- API：`POST` 当前 URL（后端 CSRF exempt），响应 `{status: success|already_confirmed|...}`

### 12.6 响应式（≤576px）

- 容器 `padding:2rem`；h1 `1.6rem`；offer-title `1.2rem`；toast 容器改为 `top/right/left:10px; max-width:none`，toast 全宽

---

## 13. 页面规格 — OAuth 回调 `callback.html`（调试页）

- 居中 `h3 正在处理登录...` + `#debug-info`（`mt-3 text-muted` 14px）调试日志区
- JS 逻辑（逐行 `log()` 输出到控制台与页面）：
  1. 依次解析 URL hash 与 query 中的 `access_token` / `state`；无 token 也无 `code` → 3s 后跳 `/login/`
  2. 若只有 `code` → 提示为 Authorization Code 模式、当前配置为 Implicit，5s 后跳 `/login/`
  3. 取得 token 后 POST `/api/save-token/`（`Content-Type: application/json` + `X-CSRFToken`，body：`{access_token, state}`）
  4. 成功且含 `redirect_url` → 500ms 后跳转；失败/网络错误 → 3s 后跳 `/login/`

---

## 14. 路由清单（复刻时需映射的 URL 与页面）

| URL | 页面 | 权限 |
|---|---|---|
| `/` | 首页 | 公开 |
| `/login/` | OAuth 跳转（触发外部登录） | 公开 |
| `/logout/` | 退出 | 登录 |
| `/oauth/callback/`、`/auth/callback/` | 回调（callback.html） | 公开 |
| `/profile/` | 个人资料 | 登录 |
| `/verify/` | 申请认证 | 登录 |
| `/verify/review/` | 认证审核 | `can_review_applications` |
| `/identity-card/` | 身份卡 | 登录 |
| `/club/` | 社团报名 | 登录 |
| `/club/status/` | 申请状态 | 登录 |
| `/club/admin/` | 社团审核 | `can_review_club_applications` |
| `/club/confirm-offer/{uuid}/` | Offer 确认（独立页） | 公开（UUID 令牌） |
| `/api/save-token/`、`/club/check-verification/`、`/club/submit/` | JSON API | 登录 |

---

## 15. 复刻校验清单（Checklist）

- [ ] CSS 变量、四种渐变体系、圆角/阴影/间距令牌与 2.x 节完全一致
- [ ] 导航栏：品牌渐变、nav-link 白 0.9 / active 白 0.2 底、登录态菜单项
- [ ] 首页 6 区块顺序、hero 双层背景、金色渐变文字、4 浮动元素错峰动画
- [ ] 卡片 hover 统一 `translateY` 抬升 + 顶部渐变条展开
- [ ] 三步向导：进度条 50% 起步、自动检查、各状态 alert、Toast 类型切换
- [ ] 申请状态页：4 节点进度条 25/50/75/100%、状态 badge、按状态分支详情
- [ ] 审核页：状态筛选、编辑模态框、confirm/SweetAlert 确认后 fetch + reload
- [ ] Offer 页：流动渐变背景、按钮 5 态状态机、自定义 Toast、Canvas 烟花（150+30 粒子）
- [ ] 响应式断点 768px / 576px 行为与 4.7 / 8.x 等节一致
- [ ] 自定义 loading 静态资源缺失，需自实现 `window.loadingManager` 等价能力
