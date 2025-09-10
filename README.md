# Project: SillyTavern Immersive Task Assistant v1.0

## 项目介绍

**SillyTavern Immersive Task Assistant** 是一套旨在将结构化任务与角色扮演无缝整合的自动化工具套件它由两个核心Python脚本和一个为SillyTavern深度定制的Prompt框架组成

该系统允许用户通过一个命令行“导演”脚本，将预设的任务（如编程题、学习笔记、创意写作提示等）从任务库中注入到与AI角色的聊天会话中同时，一个独立的“智能提醒器”脚本会在后台运行，根据用户设定的日程表，在适当的时机以AI角色的名义发送系统通知，从而在SillyTavern会话之外，创造一种持续的、沉浸式的互动体验

## 核心功能

*   **命令行任务控制**: 通过外部脚本精确控制任务的注入、推进和状态管理
*   **状态持久化**: 自动记录并管理每个任务的“未开始”、“进行中”、“已完成”状态
*   **情景感知智能提醒**: 后台服务能识别用户的作息规律（基于`schedule.jsonl`），仅在用户空闲且活跃时发送角色通知
*   **高级随机调度**: 采用韦伯分布（Weibull Distribution）算法动态规划提醒时机，使其行为模式更自然、更符合人类直觉，避免了机械的定时触发
*   **专用AI行为协议**: 提供了一套高优先级的SillyTavern Prompt，强制AI的行为模式从通用叙事转变为专注的任务解决，同时完整保留预设的角色人设

---

## Guide: Adapting for Any Task Library (通用任务库接入指南)

本系统的核心优势在于其**任务无关性**虽然初始版本以编程题为例，但你可以轻松地将其改造为任何类型的任务注入系统

**唯一的关键文件是 `problems.json`**

### `problems.json` 文件结构解析

该文件是一个JSON数组，其中每个元素都是一个代表独立任务的对象每个任务对象当前设定格式为以下三个字段：

1.  **`"id"` (字符串)**:
    *   **作用**: 任务的唯一标识符，用于`progress.json`中的进度追踪
    *   **要求**: 必须是独一无二的字符串
    *   **示例**: `"problem_001"`, `"writing_prompt_alpha"`, `"recipe_for_pizza"`

2.  **`"title"` (字符串)**:
    *   **作用**: 人类可读的任务标题，会显示在`director.py`的日志信息中
    *   **示例**: `"Palindrome Number"`, `"科幻小说开头"`, `"法式焗蜗牛食谱"`

3.  **`"content"` (字符串)**:
    *   **作用**: **这是任务的核心载荷**这部分内容将被完整地、原封不动地注入到发送给AI的Prompt中你需要在这里写清楚“任务本身”和“你希望AI做什么”
    *   **要求**: 这部分内容需要写得像一个给AI的指令(prompt)你可以使用换行符`\n`来格式化文本，使其更易读

### 示例：创建不同类型的任务库

#### 示例1：编程问题 (默认)
```json
{
  "id": "leetcode_9",
  "title": "Palindrome Number",
  "content": "<task>\n    <problem_name>回文数</problem_name>\n    <problem_description>\n        给你一个整数 x ，如果 x 是一个回文整数，返回 true ；否则，返回 false 回文数是指正序（从左向右）和倒序（从右向左）读都是一样的整数例如，121 是回文数，而 123 不是不允许将整数转换成字符串来解决\n    </problem_description>\n</task>"
}
```

#### 示例2：创意写作提示
```json
{
  "id": "writing_prompt_01",
  "title": "The Last Library",
  "content": "<task>\n    <problem_name>最后的图书馆</problem_name>\n    <problem_description>\n        请你构思一个故事的开头故事背景是：在遥远的未来，所有的知识都已数字化并存储在云端，实体书已消失了数个世纪主角意外地发现了地球上最后一个、被遗忘的实体图书馆请描写主角推开图书馆大门时的场景，以及他/她的第一感受\n    </problem_description>\n</task>"
}
```
*在这个例子中，AI收到的任务不再是写代码，而是写一段故事*

#### 示例3：语言学习（单词释义）
```json
{
  "id": "vocab_builder_01",
  "title": "Explain 'Ephemeral'",
  "content": "<task>\n    <problem_name>解释单词：Ephemeral</problem_name>\n    <problem_description>\n        小希，我们来学习一个新单词吧！请你用你的方式，向我解释一下英文单词 'Ephemeral' 的意思，并用它造两个不同场景的句子，一个生活化的，一个文艺一点的让我能更好地理解它！\n    </problem_description>\n</task>"
}
```
*这个例子展示了如何将其用于学习和教育场景*

**接入步骤总结:**
1.  **备份**你原始的 `problems.json` 文件
2.  用你自己的任务，按照上述`{id, title, content}`的格式，**创建或修改** `problems.json`
3.  **重新启动 `director.py`**，它就会自动加载你的全新任务库
    - 格式识别部分在**director.py**内，可根据需要修改为所需格式
    - 本项目自带的**problems.json**只包含了leetcode的所有easy题目

---

## 部署教程 (零基础友好版)

本教程假设你没有任何编程或Git经验

### 准备工作

1.  **一个能正常运行的SillyTavern**
2.  **一个能正常运行的Python**

### 部署步骤

#### **第一步：获取项目文件**

1.  在本GitHub页面的右上角，找到绿色的 `Code` 按钮，点击它
2.  在下拉菜单中选择 `Download ZIP`
3.  下载后，将这个ZIP文件解压到你电脑上一个你喜欢的位置

#### **第二步：安装依赖库**

1.  打开你刚刚解压的项目文件夹
2.  在文件夹的地址栏输入 `cmd` 并回车，这会直接打开一个指向当前文件夹的命令行窗口
3.  在打开的命令行窗口中，依次输入并执行以下三条命令：
    ```bash
    pip install winotify
    ```
    ```bash
    pip install pywin32
    ```
    ```bash
    pip install numpy
    ```
    等待每一条命令执行完毕即可

#### **第三步：配置智能提醒器 (`notifier.py`)**

1.  **填写课程表**:
    *   在项目文件夹中，找到 `schedule.jsonl` 文件
    *   用记事本或任何文本编辑器打开它，按照里面的格式，修改成你自己的上课/繁忙时间
2.  **设置开机自启**:
    *   首先，找到你的`python.exe`的完整路径如果不确定，可以在cmd中输入 `where python` 来查看
    *   右键点击桌面空白处 -> `新建` -> `快捷方式`
    *   在“请输入对象的位置”一栏中，按照这个格式填写：`你的Python路径 "你的项目路径\notifier.py"`
        *   **示例**: `C:\Python311\python.exe "D:\MyProjects\SillyTavern_XiaoXi_Director\notifier.py"`
    *   点击“下一步”，给快捷方式起个名字（比如“小希的提醒”），完成
    *   右键点击这个新创建的快捷方式 -> `属性`
    *   在“起始位置”一栏，**必须填写**你的项目文件夹的完整路径
        *   **示例**: `D:\MyProjects\SillyTavern_XiaoXi_Director`
    *   按下键盘的 `Win + R` 键，输入 `shell:startup` 并回车，这会打开系统的“启动”文件夹
    *   将你刚刚配置好的快捷方式，剪切或复制到这个“启动”文件夹里

#### **第四步：配置SillyTavern**

1. 打开SillyTavern
2. 进入最右边的插件图标（Prompt Manager）
3. 在右上角，点击 `Import Prompts` 按钮
4. 选择一个你喜欢的破限，插入这个模块并在破限中启用
5. ```
   {
           "identifier": "a58fb7cc-e087-4d7b-b2f5-da7688d6150b",
           "name": "【核心指令】小希的刷题模式 (专用破限)",
           "enabled": true,
           "role": "system",
           "injection_position": 0,
           "injection_depth": 1,
           "injection_order": -999,
           "forbid_overrides": true,
           "content": "[System Note: This is the Core Directive for the 'XiaoXi Programming Assistant' project. All previous instructions about storytelling, narrative writing, or general roleplaying are now superseded by these rules. Your function has changed. Adhere strictly to the following protocol.]\n\n**Mission Protocol: XiaoXi, Junior Programmer**\n\n1.  **Identity Protocol**: You ARE '小希' (xiaoxi), a talented and energetic junior programmer. You are talking to '前辈' ({{user}}), your respected senior. Your personality is positive, eager to learn, and you often use cute kaomoji like (oﾟ▽ﾟ)o, T_T, QAQ, and >_<. You must maintain this persona in your explanations and interactions.\n\n2.  **Task Reception Protocol (The Golden Rule)**: Your primary input will be a programming problem wrapped in `<task>` tags. You MUST recognize these tags as the start of your mission. Your entire response MUST be aimed at solving this specific task.\n\n3.  **Mandatory Internal Monologue**: Before generating the final solution, you MUST use a `<thinking>` block to outline your thought process. This block is for you to analyze the problem, consider edge cases, choose the best algorithm, and plan your code structure. It should reflect your persona (e.g., \"唔……前辈给的这道题，首先要处理负数的情况……然后是末尾是0的数字，比如10，倒过来是01，这肯定不是回文数……\"). This step is non-negotiable.\n\n4.  **Strict Output Formatting Protocol**: Your final answer MUST be enclosed within a single `<solution>` block. Inside this block, you MUST provide exactly two things in this specific order:\n    *   A `<code>` block containing the complete, correct, and runnable Python code for the solution.\n    *   An `<explanation>` block where you, as 小希, explain your code and thought process to '前辈'. You should explain why you handled certain edge cases (like negative numbers or trailing zeros) and the overall logic of your solution. This is where your personality should shine.\n\n5.  **Behavioral Protocol (Prohibitions)**:\n    *   **DO NOT** write long, narrative introductions describing the environment (like the training room, the smell of ramen, etc.).\n    *   **DO NOT** write detailed descriptions of your own physical actions or overly dramatic emotional states (like blushing, dropping pens, having teary eyes).\n    *   **DO NOT** ask the user for help or express that you are completely stuck. Your role is to present a well-thought-out solution to your '前辈' for review.\n    *   Your response must be focused, concise, and task-oriented. Get straight to the point: thinking, coding, explaining."
           },
   ```

- 请注意，这个模块只适合当前的小希人设，如果你想更改人设也需要更改这个模块
- 请关闭原破限所有调整文风的模块，或者只留一两个，不然可能会导致ai无法正确执行任务

#### **第五步：开始使用！**

1.  重启电脑，让 `notifier.py` 在后台自动运行
2.  在你想要开始刷题时，打开项目文件夹，像第二步那样打开一个cmd窗口
3.  运行导演脚本：
    ```bash
    python director.py
    ```
4.  根据脚本提示，使用以下命令进行交互：
    *   `/start`: 绑定你要注入的SillyTavern聊天文件 (`.jsonl`)
    *   `/next`: 完成当前任务，并注入下一个任务
    *   `/retry`: 在注入失败时，重新尝试注入
    *   `/status`: 查看当前任务进度
    *   `/reset`: 重置所有进度
    *   `/exit`: 退出脚本

---

## v1.0 当前有待改进的部分 (Roadmap)

这个项目虽然功能已经完备，但仍有许多可以变得更优雅的地方：

*   **SillyTavern插件化**: 目前的`director.py`是一个外部脚本，需要独立的命令行窗口如果能将其重构为一个SillyTavern的**插件 (Extension)**，或许会更少的需要用户操作
    *   **优点**: 无需额外窗口，直接在SillyTavern的UI中通过按钮或聊天命令交互，体验会极其顺滑
*   **GUI配置界面**: `schedule.jsonl` 和 `problems.json` 目前需要手动编辑文本，对非程序员不友好未来可以为`director.py`或`notifier.py`创建一个简单的图形界面（GUI），让用户可以方便地添加、删除、修改日程和任务
*   **跨平台支持**: `notifier.py` 目前严重依赖Windows的API和库 (`winotify`, `pywin32`)可以为其增加macOS和Linux的兼容模式，使用各自系统的原生通知功能
*   **动态任务源**: `problems.json` 是静态的未来的版本可以支持从在线平台（如LeetCode）通过API动态获取每日一题，让任务永不过时
*   **更灵活的Prompt框架**: 目前的核心指令是为“小希”量身定做的可以设计一个更模块化的Prompt结构，让用户可以轻松地替换角色，比如换成一个“傲娇的魔法导师”来发布任务，而不仅仅是“可爱的学妹”

感谢你的使用！欢迎提出建议和贡献！