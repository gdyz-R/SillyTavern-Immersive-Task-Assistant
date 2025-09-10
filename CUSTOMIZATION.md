# Advanced Customization & Developer Guide

欢迎来到高级配置区！本文档旨在帮助你完全掌控 **Immersive Task Assistant** 的每一个细节，将其从“小希的刷题助手”改造为你想要的任何东西

我们将改装过程分为四个级别，从简单到复杂：

-   **Level 1**: 修改任务内容 (数据库)
-   **Level 2**: 修改AI的人设与行为 (灵魂)
-   **Level 3**: 修改智能提醒器的风格 (陪伴)
-   **Level 4**: 修改核心脚本逻辑 (框架)

---

## Level 1: Customizing the Task Library (`problems.json`)

这是最基础也是最核心的自定义本系统支持任何类型的结构化任务

唯一的关键文件是 `problems.json`它是一个标准的JSON数组，每个元素都是一个代表任务的对象

### 任务对象的统一结构

每个任务对象**必须包含**以下三个字段：

```json
{
  "id": "一个独一-无二的字符串ID",
  "title": "一个方便你识别的任务标题",
  "content": "将要发送给AI的具体指令内容"
}
```

当前数据库的格式非常适合作为简单，纯粹的的题库，如果需要更详细的分类，需要修改director识别部分以及注入部分代码


---

## Level 2: Modifying the AI's Persona and Behavior (The Soul)

这是最有趣的自定义部分AI的“灵魂”由两部分共同决定：**角色卡** 和 **核心指令 (`prompts/core.json`)**

-   **角色卡**: 定义了AI的**基础人设**（它是谁，它的性格、背景、说话风格）
-   **核心指令**: 定义了AI在本项目中的**行为准则**（它必须做什么，必须说什么格式的话）

**两者必须协同修改，才能达到完美效果**

### 1. 修改角色卡

-   在SillyTavern中，编辑或替换你当前使用的角色卡
-   **示例**: 你想把“ energetic junior programmer 小希”换成“a strict, cold senior professor 教授林”
    -   你需要修改角色卡的`Name`
    -   修改`Description`，描述林教授的背景、性格（严厉、博学、不苟言笑）
    -   修改`Greeting`，让她的开场白符合人设

### 2. 修改核心指令 (`prompts/core.json`)

用文本编辑器打开`prompts/core.json`文件，找到`"content"`字段里面的长文本就是AI的行为准则

**关键修改点**：

-   **`Identity Protocol`**:
    -   将`You ARE '小希' (xiaoxi)`修改为`You ARE '林教授' (Professor Lin)`
    -   修改后面的描述，使其与你的新角色卡人设一致例如，将`energetic junior programmer`改为`a respected, knowledgeable but strict computer science professor`

-   **`Mandatory Internal Monologue`**:
    -   修改`<thinking>`块中的示例文本将`“唔……前辈给的这道题……”`改为符合新角色风格的思考，例如`“哼，这道基础题首先，必须检查输入参数的有效性其次，要考虑边界条件……”`这会强烈地引导AI模仿这种思考模式

-   **`Strict Output Formatting Protocol`**:
    -   在`<explanation>`部分的描述中，修改`as 小希, explain your code...`为`as 林教授, explain the code...`

**重要提示**: 除非你清楚自己在做什么，否则**不要**修改`content`中的输出结构要求，如`<thinking>`, `<solution>`, `<code>`, `<explanation>`这些标签`director.py`依赖这些标签来解析AI的回复

---

## Level 3: Customizing the 'Living' Companion (`notifier.py`)

你可以让后台的智能提醒器完全符合你的新角色人设

打开`notifier.py`进行编辑：

### 1. 修改提醒消息 (`messages` 列表)
找到`messages`列表，将其中的内容替换为符合你新角色性格的句子
-   **示例 (林教授)**:
    ```python
    messages = [
        "你的进度有点慢，今天研究一下这个问题",
        "我刚才想到了一个算法上的优化点，记下来，有空看看",
        "不要松懈，保持思考的习惯",
        "基础不牢，地动山摇复习一下这个知识点",
        "这张知识图谱对你的学习有帮助"
    ]
    ```

### 2. 修改启动画面 (`XIAOXI_LOGO` 变量)
你可以去 [patorjk.com/software/taag/](http://patorjk.com/software/taag/) 这类网站，生成一个符合新角色名字的ASCII art，替换掉`XIAOXI_LOGO`的内容

### 3. 调整提醒“性格” (韦伯分布参数)
这是最高级的定制，你可以调整AI提醒的“积极性”

-   `WEIBULL_SHAPE` (形状参数 k):
    -   `k > 1`: 概率随时间递增 (空闲越久，越可能提醒你，这是默认的“小希”模式，`k=2.0`)
    -   `k = 1`: 概率恒定 (纯随机，无记忆)
    -   对于**林教授**这样严格的角色，可以设置`k=1.0`，代表她只是在随机抽查，而不是“越来越想你”

-   `WEIBULL_SCALE_MINUTES` (尺度参数 λ):
    -   这是“平均”的提醒间隔默认是`90.0`分钟
    -   如果你希望林教授“抽查”得更频繁，可以减小这个值，比如`60.0`

---

## Level 4: Advanced Scripting (For Developers)

如果你熟悉Python，可以对核心脚本进行修改

### `director.py` 的可扩展点

-   **修改命令**: 你可以轻易地修改`/start`, `/next`等命令为你喜欢的任何词
-   **集成API**:
    -   修改`find_and_read_problems`函数，使其不再从本地`problems.json`读取，而是通过API请求从一个在线题库（如LeetCode API）获取
    -   在`inject_task_into_chat`函数成功后，增加一个webhook调用，将“任务完成”状态发送到Discord或Slack
-   **改变日志格式**: 修改脚本中的`print`语句，以你喜欢的格式输出日志

### `notifier.py` 的可扩展点

-   **跨平台支持**:
    -   在脚本开头增加平台检测 (`sys.platform`)
    -   为`darwin` (macOS) 和 `linux` 编写新的通知函数，使用`os.system`调用各自平台的原生通知命令（如`osascript`或`notify-send`），替换掉`winotify`的部分
-   **动态消息源**:
    -   修改`send_xiaoxi_notification`函数，使其不再从固定的`messages`列表中随机选择，而是通过API从一个“每日一句”网站或你自己的服务器获取消息内容