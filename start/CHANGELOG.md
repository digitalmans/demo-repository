# 修改说明文档

> **日期**：2026-07-06
> **范围**：本次会话内的两处 bug 修复
> **项目**：`demo-repository-fresh-copy`（Flask + MySQL 8，讨论区社区化升级之后）

---

## 修复一：讨论区加载报 `discussions is not defined`

### 现象
访问讨论区页面（`/qa_discussion`）时，控制台报错：

```
网络错误: disussions is not defined
```

页面停留在"暂无讨论，快来发布第一条吧！"占位文案，但实际数据库里有数据，API 也能正常返回。

### 根因
`start/templates/qa_discussion_content.html` 第 179、184 行，JavaScript 变量名拼写错误。

```javascript
function displayDiscussions(discussions, reset=false) {  // 形参：discussions（11 字符，d-i-s-c-u-s-s-i-o-n-s）
    const container = document.getElementById('discussions-container');
    if (reset) container.innerHTML = '';
    if (discussions.length === 0 && reset) {              // ← 错别字：disussions（10 字符，少了 c）
        container.innerHTML = '<div style="...">暂无讨论，快来发布第一条吧！</div>';
        return;
    }
    if (discussions.length === 0) return;                // ← 同样错别字
    const html = discussions.map(renderDiscussionCard).join('');
    container.insertAdjacentHTML('beforeend', html);
}
```

形参是 `discussions`，函数体内两处写成了 `disussions`（10 字符的错别字），浏览器 JS 引擎找不到这个变量就抛 `ReferenceError`，导致整个讨论列表渲染中断，停留在空状态的兜底文案上。

### 修复
把第 179、184 行的 `disussions.length` 改为 `discussions.length`。

### 验证
- 模板里 `discussions`（错别字）出现 0 次
- 正确的 `discussions` 出现 10 次
- `curl /api/qa_discussion/feed?sort=hot` 返回 8 条讨论，🔥 热度排序正确（id=3 因 3 赞排第一）

---

## 修复二：个人主页显示「用户不存在」

### 现象
点击侧边栏「我的主页」或访问 `/user/cjw`，页面显示：

```
用户不存在
```

但后端 API `/api/user/cjw/profile` 调用正常（HTTP 200，返回 cjw 的完整 profile 数据）。

### 根因
`start/templates/user_profile.html` 第 70-71 行，Jinja2 模板存在**双重编码**反模式：

```jinja
<script>
const profileUsername = {{ ('"%s"' % profile_username)|tojson }};
const currentUsername = {{ ('"%s"' % session.get('username',''))|tojson }};
const isSelf = currentUsername === profileUsername;
```

执行流程：
1. Python 端 `'"%s"' % 'cjw'` → `'"cjw"'`（5 字符的字符串 ` "cjw" `，**已经带双引号了**）
2. `|tojson` 把它当 JSON 字符串再编码一次 → 输出 `"\"cjw\""`（带转义的双引号）

最终 JS 渲染出来的不是 `cjw`，而是 6 字符的字符串 `"cjw"`：

```javascript
const profileUsername = "\"cjw\"";   // 字面意义是 "cjw"（带引号），共 6 字符
```

后续 `fetch` 拼出来的 URL 变成：

```
/api/user/%22cjw%22/profile        // %22 是 " 的 URL 编码
```

后端按 `"cjw"`（带引号）去 `users` 表查，命中 0 行，返回 `{"success": false, "error": "用户不存在"}`。

### 修复
直接用 `|tojson`，它本身就会正确加引号 + 转义，不需要外面再手动拼 `'"%s"'`：

```jinja
const profileUsername = {{ profile_username|tojson }};
const currentUsername = {{ session.get('username','')|tojson }};
```

### 同病相怜
`start/templates/qa_discussion_content.html` 第 113 行有完全一样的反模式，一并修复：

```diff
- const currentUsername = {{ ('"%s"' % session.get('username',''))|tojson }};
+ const currentUsername = {{ session.get('username','')|tojson }};
```

### 验证
- 模板渲染后输出 `const profileUsername = "cjw";`（3 字符，正确）
- `curl /api/user/cjw/profile` 返回：
  ```json
  {
    "success": true,
    "profile": {
      "user":  {"id": 3, "username": "cjw", "role": "user"},
      "stats": {"discussion_count": 2, "comment_count": 1, "total_likes": 0, "total_views": 3, "favorite_count": 0}
    }
  }
  ```

---

## 修改文件清单

| 文件 | 类型 | 改动 |
|---|---|---|
| `start/templates/qa_discussion_content.html` | 修改 | 第 179、184 行：错别字 `disussions` → `discussions`<br>第 113 行：双重编码反模式修复 |
| `start/templates/user_profile.html` | 修改 | 第 70-71 行：双重编码反模式修复 |

无数据库 schema 变更，无后端路由变更，无新增依赖。

---

## 经验教训

### 1. JS 拼写错误难以发现，因为没有编译期检查
- JS 变量名拼错只会到运行时才暴露，模板里很容易漏
- 经验：写 JS 时尽量避免长变量名（`discussions` 这种），或者把渲染逻辑搬到独立 JS 文件做语法 lint

### 2. Jinja2 `|tojson` 是"包字符串字面量"，不是"再编码一次"
- `|tojson` 等价于 `JSON.stringify`，**自动加双引号 + 转义**
- 不要再外面手拼 `'"%s"' % xxx`，那是二次编码
- 反模式搜索关键词：`("'%s'" %` / `('"%s"' %` / `(\"%s\" %)`

### 3. 修 bug 时的"老手"陷阱
- 我在 Edit 工具的 `old_string` 里反复手打 `discussions` 错别字，5-6 次都匹配不上
- 最后用 Python 变量拼接 `typo = 'dis' + 'u' + 'ssions'` 才匹配上
- 经验：遇到容易拼错的字符串，用 Python `str.replace` 走 `/tmp` 副本 + `cp` 回原位，比 Edit 更稳
