import json
import os
import sys
import tempfile
import shutil
import time
from datetime import datetime

# (放在文件顶部)
try:
    import winsound
    from winotify import Notification
    IS_WINDOWS = True
except ImportError:
    IS_WINDOWS = False


# --- 颜色常量 ---
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    CYAN = '\033[96m'
    ENDC = '\033[0m'


# --- 文件常量 ---
PROBLEMS_FILE = 'problems.json'
PROGRESS_FILE = 'progress.json'
# <--- 新增: SillyTavern 聊天记录的基础路径，请根据你的实际情况修改 ---
SILLY_TAVERN_CHATS_BASE_PATH = "C:\\SillyTavern\\data\\default-user\\chats"


# --- 辅助函数 ---


def log_success(message):
    """打印成功的日志信息"""
    print(f"{Colors.GREEN}[SUCCESS] {message}{Colors.ENDC}")


def log_error(message):
    """打印错误的日志信息"""
    print(f"{Colors.RED}[ERROR] {message}{Colors.ENDC}")


def log_info(message):
    """打印提示性的日志信息"""
    print(f"{Colors.CYAN}[INFO] {message}{Colors.ENDC}")


def log_warning(message):
    """打印警告的日志信息"""
    print(f"{Colors.YELLOW}[WARNING] {message}{Colors.ENDC}")


def atomic_write_json(data, filepath):
    """
    以原子方式将JSON数据写入文件。
    先写入临时文件，然后重命名，防止数据损坏。
    """
    try:
        # 创建一个与目标文件在同一目录下的临时文件
        temp_fd, temp_path = tempfile.mkstemp(dir=os.path.dirname(os.path.abspath(filepath)))
        with os.fdopen(temp_fd, 'w') as temp_file:
            json.dump(data, temp_file, indent=2, ensure_ascii=False)
        
        # 将临时文件重命名为目标文件，这是一个原子操作
        shutil.move(temp_path, filepath)
        return True
    except Exception as e:
        log_error(f"写入文件 {filepath} 失败: {e}")
        # 如果临时文件仍然存在，则清理
        if 'temp_path' in locals() and os.path.exists(temp_path):
            os.remove(temp_path)
        return False


def load_problems():
    """从 problems.json 加载所有题目到一个字典中"""
    try:
        problems = {}
        with open(PROBLEMS_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                problem_data = json.loads(line)
                problems.update(problem_data)
        return problems
    except FileNotFoundError:
        log_error(f"题库文件 '{PROBLEMS_FILE}' 未找到。请确保它与脚本在同一目录下。")
        sys.exit(1)
    except json.JSONDecodeError:
        log_error(f"题库文件 '{PROBLEMS_FILE}' 格式错误，请检查是否为有效的JSON Lines格式。")
        sys.exit(1)


def initialize_progress_file():
    """
    当 progress.json 不存在时，创建并初始化它。
    读取 problems.json 并将所有题目ID填充到 'not_started' 列表。
    """
    log_info(f"'{PROGRESS_FILE}' 未找到，正在进行首次初始化...")
    
    # 加载所有题目以获取ID
    all_problems = load_problems()
    all_problem_ids = list(all_problems.keys())
    
    initial_data = {
        "session_info": {
            "active_chat_file": None
        },
        "tasks": {
            "not_started": all_problem_ids,
            "in_progress": [],
            "completed": []
        }
    }
    
    if atomic_write_json(initial_data, PROGRESS_FILE):
        log_success(f"'{PROGRESS_FILE}' 初始化成功，加载了 {len(all_problem_ids)} 道题目。")
        return initial_data
    else:
        log_error("初始化失败，无法创建进度文件。请检查目录权限。")
        sys.exit(1)


# --- 命令处理函数 ---


def handle_start(progress_data, all_problems):
    """
    <--- MODIFIED: 实现路径自动填充 ---
    处理 /start 命令
    """
    raw_input = input("请输入SillyTavern聊天记录文件路径 (可以是简称, 如 'xiaoxi - 2025-09-09@20h27m39s'): ").strip()
    
    chat_file_path = ""
    # 判断输入的是否是完整路径
    if '\\' in raw_input or '/' in raw_input:
        chat_file_path = raw_input
    else:
        # 尝试从简称构建路径
        try:
            # 假设格式是 "角色名 - 日期..."
            char_name = raw_input.split(' - ')[0]
            filename = f"{raw_input}.jsonl"
            chat_file_path = os.path.join(SILLY_TAVERN_CHATS_BASE_PATH, char_name, filename)
            log_info(f"检测到简称，已自动填充路径为: {chat_file_path}")
        except IndexError:
            log_error("无法从简称中解析角色名。请输入完整路径或使用 '角色名 - 日期' 格式的简称。")
            return progress_data

    if not os.path.isfile(chat_file_path):
        log_error(f"路径 '{chat_file_path}' 无效或不是一个文件。")
        return progress_data

    if not os.access(chat_file_path, os.R_OK) or not os.access(chat_file_path, os.W_OK):
        log_error(f"文件 '{chat_file_path}' 不可读或不可写，请检查文件权限。")
        return progress_data
        
    progress_data["session_info"]["active_chat_file"] = os.path.abspath(chat_file_path)
    
    if atomic_write_json(progress_data, PROGRESS_FILE):
        log_success(f"会话已成功绑定到: {os.path.abspath(chat_file_path)}")
    else:
        return progress_data # 如果写入失败，则不继续

    # 检查联动：如果已有进行中的任务，则重新注入
    if progress_data["tasks"]["in_progress"]:
        current_task_id = progress_data["tasks"]["in_progress"][0]
        log_info(f"检测到正在进行的任务 '{current_task_id}'，正在将其重新注入新的聊天文件...")
        # 调用注入函数，这里不需要关心返回值，因为只是恢复状态
        inject_task_to_chat(current_task_id, progress_data["session_info"]["active_chat_file"], all_problems)
    
    return progress_data


def inject_task_to_chat(problem_id, chat_file_path, all_problems):
    """
    <--- MODIFIED: 增加延时和验证重试逻辑 ---
    将指定的任务作为<task>块注入到聊天文件中。
    """
    problem_details = all_problems.get(problem_id)
    if not problem_details:
        log_error(f"无法在 '{PROBLEMS_FILE}' 中找到题目ID: {problem_id}")
        return False

    # 1. 构建<task>指令块 (代码无变化)
    task_xml = (
        f"<task>\n"
        f"    <problem_name>{problem_details['title']}</problem_name>\n"
        f"    <problem_description>\n"
        f"        {problem_details['description']}\n"
        f"    </problem_description>\n"
        f"</task>"
    )

    # 2. 封装成符合SillyTavern格式的JSON对象 (代码无变化)
    send_time = datetime.now().strftime("%B %d, %Y %I:%M%p").replace("AM", "am").replace("PM", "pm")
    parts = send_time.split()
    if len(parts) > 2 and parts[1].endswith(','): # Handle cases like 'September 09,'
        day_part = parts[1][:-1]
        if day_part.startswith('0'):
            parts[1] = day_part[1:] + ','
    send_time = ' '.join(parts)
    
    message_record = {
        "name": "User",
        "is_user": True,
        "is_system": False,
        "send_date": send_time,
        "mes": task_xml,
        "extra": {}
    }

    # 3. 执行“读取-修改-写入”的可靠注入流程
    try:
        lines = []
        if os.path.exists(chat_file_path):
            with open(chat_file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        
        new_line = json.dumps(message_record, ensure_ascii=False) + '\n'
        lines.append(new_line)

        temp_fd, temp_path = tempfile.mkstemp(dir=os.path.dirname(os.path.abspath(chat_file_path)))
        with os.fdopen(temp_fd, 'w', encoding='utf-8') as temp_file:
            temp_file.writelines(lines)
        
        shutil.move(temp_path, chat_file_path)

        # 4. 【关键修改】加入延时和验证重试循环
        max_retries = 5
        for i in range(max_retries):
            time.sleep(0.1 * (i + 1)) # 每次等待时间递增: 0.1s, 0.2s, ...
            try:
                with open(chat_file_path, 'r', encoding='utf-8') as f:
                    final_lines = f.readlines()
                
                if final_lines and final_lines[-1].strip() == new_line.strip():
                    return True # 验证成功，立即返回
            except Exception as read_e:
                log_warning(f"验证时读取文件失败 (尝试 {i+1}/{max_retries}): {read_e}")

        # 如果循环结束仍未成功
        log_error("验证失败！文件内容在写入后没有按预期更新。")
        return False

    except Exception as e:
        log_error(f"向聊天文件注入任务时发生严重错误: {e}")
        if 'temp_path' in locals() and os.path.exists(temp_path):
            os.remove(temp_path)
        return False


def handle_next(progress_data, all_problems):
    """
    处理 /next 命令。
    此函数逻辑基本不变，但它的返回值将影响 main 循环中的 task_to_retry_id。
    """
    if not progress_data["session_info"]["active_chat_file"]:
        log_error("未设置活动的聊天文件。请先使用 /start 命令。")
        return progress_data, None # <--- MODIFIED: 返回 None 表示没有要重试的任务

    if not progress_data["tasks"]["not_started"]:
        log_success("恭喜！所有题目均已完成！")
        if progress_data["tasks"]["in_progress"]:
            completed_task_id = progress_data["tasks"]["in_progress"].pop(0)
            progress_data["tasks"]["completed"].append(completed_task_id)
            atomic_write_json(progress_data, PROGRESS_FILE)
        return progress_data, None # <--- MODIFIED

    next_task_id = progress_data["tasks"]["not_started"][0]
    
    log_info(f"正在尝试注入新任务: '{all_problems.get(next_task_id, {}).get('title', '未知')}'...")
    is_injected = inject_task_to_chat(
        next_task_id, 
        progress_data["session_info"]["active_chat_file"], 
        all_problems
    )

    if is_injected:
        log_success(f"任务 '{all_problems[next_task_id]['title']}' 已成功注入并通过验证。")
        # 注入成功，更新进度
        if progress_data["tasks"]["in_progress"]:
            completed_task_id = progress_data["tasks"]["in_progress"].pop(0)
            progress_data["tasks"]["completed"].append(completed_task_id)
            log_info(f"任务 '{completed_task_id}' 已标记为完成。")

        progress_data["tasks"]["not_started"].pop(0)
        progress_data["tasks"]["in_progress"].append(next_task_id)
        
        atomic_write_json(progress_data, PROGRESS_FILE)
        return progress_data, None # <--- MODIFIED: 注入成功，清空重试任务
    else:
        # 注入失败
        log_error("任务注入失败。进度未作任何更改。")
        log_warning("请检查文件权限或SillyTavern是否完全锁定了文件。")
        log_info("你可以使用 /retry 命令重新尝试注入当前任务。")
        return progress_data, next_task_id # <--- MODIFIED: 返回失败的任务ID以供重试


def handle_notify_test():
    """处理 /notify_test 命令"""
    log_info("正在发送测试通知...")
    
    if not IS_WINDOWS:
        log_error("此功能仅在Windows系统上可用，且需要安装 'winotify' 库。")
        return
        
    try:
        toast = Notification(app_id="Director.py Script",
                             title="导演脚本测试通知",
                             msg="这是一条来自 Director.py 的测试消息！",
                             duration="short")
        toast.show()
        
        sound_file_path = 'C:\\Windows\\Media\\Windows Proximity Notification.wav'
        if os.path.exists(sound_file_path):
             winsound.PlaySound(sound_file_path, winsound.SND_FILENAME)
        else:
             winsound.MessageBeep() # 如果找不到文件，则播放默认声音

        log_success("测试通知已发送，请检查你的系统弹窗。")
        
    except Exception as e:
        log_error(f"发送通知时出错: {e}")
        log_warning("请确保你已通过 'pip install winotify' 安装了所需库。")


def handle_retry(progress_data, all_problems, task_id_to_retry):
    """
    <--- MODIFIED: 重构 retry 逻辑 ---
    处理 /retry 命令，重新注入指定ID的任务
    """
    chat_file = progress_data["session_info"]["active_chat_file"]
    if not chat_file:
        log_error("未设置活动的聊天文件。请先使用 /start 命令。")
        return progress_data, task_id_to_retry # 保持状态

    if not task_id_to_retry:
        log_error("当前没有失败的任务可供重试。请使用 /next 开启新任务。")
        return progress_data, task_id_to_retry

    retry_title = all_problems.get(task_id_to_retry, {}).get('title', '未知')
    log_info(f"正在重新尝试注入任务: '{retry_title}'...")
    
    is_injected = inject_task_to_chat(task_id_to_retry, chat_file, all_problems)

    if is_injected:
        log_success(f"任务 '{retry_title}' 已通过重试成功注入并通过验证。")
        # 重试成功后，需要执行和/next成功时一样的进度更新逻辑
        if progress_data["tasks"]["in_progress"]:
            completed_task_id = progress_data["tasks"]["in_progress"].pop(0)
            progress_data["tasks"]["completed"].append(completed_task_id)
            log_info(f"任务 '{completed_task_id}' 已标记为完成。")

        # 确保要重试的任务仍在 not_started 列表中
        if task_id_to_retry in progress_data["tasks"]["not_started"]:
            progress_data["tasks"]["not_started"].remove(task_id_to_retry)
            progress_data["tasks"]["in_progress"].append(task_id_to_retry)
            atomic_write_json(progress_data, PROGRESS_FILE)
        else:
            log_warning(f"任务 '{task_id_to_retry}' 已不在 'not_started' 列表中，可能状态已更新。")

        return progress_data, None # 重试成功，清空重试ID
    else:
        log_error(f"重试注入任务 '{retry_title}' 失败。")
        return progress_data, task_id_to_retry # 保持重试ID


def handle_status(progress_data, all_problems):
    """处理 /status 命令"""
    chat_file = progress_data["session_info"]["active_chat_file"]
    tasks = progress_data["tasks"]
    
    log_info("--- 当前会话状态 ---")
    
    if chat_file:
        print(f"  {Colors.CYAN}聊天文件:{Colors.ENDC} {chat_file}")
    else:
        print(f"  {Colors.YELLOW}聊天文件:{Colors.ENDC} 尚未绑定 (请使用 /start)")
        
    if tasks["in_progress"]:
        current_id = tasks["in_progress"][0]
        current_title = all_problems.get(current_id, {}).get('title', '未知标题')
        print(f"  {Colors.CYAN}当前题目:{Colors.ENDC} {current_title} (ID: {current_id})")
    else:
        print(f"  {Colors.CYAN}当前题目:{Colors.ENDC} 无")
        
    print(f"  {Colors.CYAN}进度统计:{Colors.ENDC} "
          f"{Colors.GREEN}已完成 {len(tasks['completed'])} 道{Colors.ENDC} | "
          f"{Colors.YELLOW}未开始 {len(tasks['not_started'])} 道{Colors.ENDC}")
    log_info("--------------------")


def handle_reset(progress_data):
    """处理 /reset 命令"""
    confirm = input(f"{Colors.YELLOW}[WARNING] 这个操作将清空所有刷题记录，并按时间戳备份当前进度。\n确定要继续吗？ (输入 'yes' 确认): {Colors.ENDC}").strip().lower()
    
    if confirm != 'yes':
        log_info("操作已取消。")
        return progress_data

    if os.path.exists(PROGRESS_FILE):
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        backup_filename = f"progress.json.{timestamp}.bak"
        try:
            shutil.move(PROGRESS_FILE, backup_filename)
            log_info(f"旧的进度文件已备份为: '{backup_filename}'")
        except Exception as e:
            log_error(f"备份进度文件失败: {e}")
            log_info("重置操作中止。")
            return progress_data

    new_progress_data = initialize_progress_file()
    
    log_success("所有刷题记录已成功重置。")
    log_warning("请使用 /start 命令重新绑定你的聊天文件。")

    return new_progress_data


# --- 主程序 ---
def main():
    """主程序循环"""
    
    if os.path.exists(PROGRESS_FILE):
        try:
            with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
                progress_data = json.load(f)
        except json.JSONDecodeError:
            log_error(f"'{PROGRESS_FILE}' 文件已损坏。请修复或删除它后重试。")
            sys.exit(1)
    else:
        progress_data = initialize_progress_file()

    all_problems = load_problems()

    if not progress_data["session_info"]["active_chat_file"]:
        log_warning("当前没有绑定的聊天文件。请使用 /start 命令来初始化会话。")

    log_info("Director.py 已启动。输入 /help 查看可用命令。")

    # <--- MODIFIED: 新增状态变量来跟踪需要重试的任务 ---
    task_to_retry_id = None

    while True:
        try:
            command = input("> ").strip().lower()
            if command == '/start':
                progress_data = handle_start(progress_data, all_problems)
                task_to_retry_id = None # 开始新的会话时，清空重试状态
            elif command == '/next':
                progress_data, task_to_retry_id = handle_next(progress_data, all_problems)
            elif command == '/status':
                handle_status(progress_data, all_problems)
            elif command == '/retry':
                # <--- MODIFIED: retry 命令现在需要 task_to_retry_id ---
                progress_data, task_to_retry_id = handle_retry(progress_data, all_problems, task_to_retry_id)
            elif command == '/reset':
                progress_data = handle_reset(progress_data)
                task_to_retry_id = None # 重置后清空重试状态
            elif command == '/notify_test':
                handle_notify_test()
            elif command == '/help':
                log_info("可用命令: /start, /next, /retry, /status, /reset, /notify_test, /exit")
            elif command == '/exit':
                log_info("正在退出...")
                break
            elif command == '':
                continue
            else:
                log_error(f"未知命令: '{command}'。输入 /help 查看可用命令。")
        except KeyboardInterrupt:
            print("\n") # 捕获 Ctrl+C
            log_info("检测到中断，正在退出...")
            break
        except Exception as e:
            log_error(f"发生了一个意外错误: {e}")

if __name__ == '__main__':
    main()