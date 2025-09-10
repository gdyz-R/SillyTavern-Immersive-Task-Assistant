import os
import json
import random
import time
from datetime import datetime, date, timedelta
import winsound
import ctypes
import numpy as np # 导入 numpy

# --- 颜色常量 ---
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    CYAN = '\033[96m'
    ENDC = '\033[0m'

try:
    from winotify import Notification
    IS_WINOTIFY_AVAILABLE = True
except ImportError:
    IS_WINOTIFY_AVAILABLE = False

# --- 全局配置 ---
SOUND_FILE_PATH = r'C:\Windows\Media\Windows Proximity Notification.wav'
PERSISTENCE_FILE = 'last_notification_date.txt'
SCHEDULE_FILE = 'schedule.jsonl'

# --- 韦伯分布高级配置 ---
# 形状参数 k: k > 1 表示概率随时间递增。k=2 是一个很好的起点，感觉很自然。
WEIBULL_SHAPE = 2.0
# 尺度参数 λ (分钟): 这是“特征寿命”。可以理解为“大约在这个时间点附近，提醒的概率最高”。
# 我们设为90分钟，意味着提醒通常会在你空闲后的1-2小时内发生。
WEIBULL_SCALE_MINUTES = 90.0
# 安全阈值 (分钟): 为避免极端情况，设置一个最长等待时间。
MAX_WAIT_MINUTES = 240 # 4小时

# --- 字符画 Logo ---
XIAOXI_LOGO = r"""
   ____            U  ___ u  _   _                  __  __   __  __  
U /"___|u   ___     \/"_ \/ | \ |"|       ___       \ \/"/   \ \/"/  
\| |  _ /  |_"_|    | | | |<|  \| |>     |_"_|      /\  /\   /\  /\  
 | |_| |    | | .-,_| |_| |U| |\  |u      | |      U /  \ u U /  \ u  
  \____|  U/| |\u\_)-\___/  |_| \_|     U/| |\u     /_/\_\   /_/\_\  
  _)(|_.-,_|___|_,-.  \\    ||   \\,-.-,_|___|_,-.,-,>> \\_,-,>> \\_  
 (__)__)\_)-' '-(_/  (__)   (_")  (_/ \_)-' '-(_/  \_)  (__)\_)  (__)  
"""

# --- 核心功能函数 (与之前版本相同，这里省略以保持清晰) ---
def load_schedule():
    schedule = {}
    try:
        with open(SCHEDULE_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                data = json.loads(line)
                schedule[data['date']] = data['occupied_slots']
        print(f"{Colors.GREEN}课程表加载成功，共 {len(schedule)} 天的计划。{Colors.ENDC}")
        return schedule
    except FileNotFoundError:
        print(f"{Colors.YELLOW}[警告] 未找到课程表文件 '{SCHEDULE_FILE}'。{Colors.ENDC}")
        return {}
    except Exception as e:
        print(f"{Colors.YELLOW}[错误] 加载课程表时出错: {e}{Colors.ENDC}")
        return {}

def is_currently_busy(now, schedule):
    today_str = now.strftime("%Y-%m-%d")
    if today_str not in schedule: return False
    busy_slots = schedule[today_str]
    for slot in busy_slots:
        try:
            start_str, end_str = slot.split('-')
            start_time = datetime.strptime(f"{today_str} {start_str}", "%Y-%m-%d %H:%M").time()
            end_time = datetime.strptime(f"{today_str} {end_str}", "%Y-%m-%d %H:%M").time()
            if start_time <= now.time() <= end_time: return True
        except ValueError: continue
    return False

def is_workstation_unlocked():
    user32 = ctypes.windll.User32
    return user32.GetForegroundWindow() != 0

def send_xiaoxi_notification():
    messages = [ "前辈，在忙吗？要不要休息一下呀~", "突然想到一个问题...不过还是不打扰前辈好了 QAQ", "今天也要加油呀！(oﾟ▽ﾟ)o", "路过~ 顺便跟前辈打个招呼！", "不知道为什么，突然就想跟前辈说句话~ 嘿嘿" ]
    chosen_message = random.choice(messages)
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {Colors.GREEN}触发提醒: '{chosen_message}'{Colors.ENDC}")
    try:
        if os.path.exists(SOUND_FILE_PATH): winsound.PlaySound(SOUND_FILE_PATH, winsound.SND_FILENAME)
        else: winsound.Beep(1000, 300)
        if IS_WINOTIFY_AVAILABLE:
            toast = Notification(app_id="来自小希的问候", title="小希发来一条消息~", msg=chosen_message, duration="short")
            toast.show()
    except Exception as e: print(f"[错误] 发送通知时发生异常: {e}")

def load_last_run_date():
    try:
        with open(PERSISTENCE_FILE, 'r') as f: return date.fromisoformat(f.read().strip())
    except (FileNotFoundError, ValueError): return date.today() - timedelta(days=1)

def save_last_run_date():
    with open(PERSISTENCE_FILE, 'w') as f: f.write(date.today().isoformat())

# --- 主程序 ---
def main():
    if os.name == 'nt': os.system('cls')
    print(Colors.CYAN + XIAOXI_LOGO + Colors.ENDC)
    print("======================================================")
    print(f"{Colors.GREEN}小希的每日提醒脚本已启动 (智能韦伯调度模式)...{Colors.ENDC}")
    schedule = load_schedule()
    print("本窗口将在 3 秒后自动开始后台监控。")
    print("======================================================")
    time.sleep(3)
    
    print("\n监控已开始，等待空闲时机...\n")

    # --- 全新的状态变量 ---
    free_since_timestamp = None
    scheduled_notification_time = None

    while True:
        now = datetime.now()
        
        # 1. 基本条件检查: 今天是否已提醒过？电脑是否解锁？
        if load_last_run_date() >= now.date() or not is_workstation_unlocked():
            free_since_timestamp = None # 只要不满足条件，就重置空闲计时
            scheduled_notification_time = None
            time.sleep(60)
            continue
            
        # 2. 检查当前是否繁忙
        if is_currently_busy(now, schedule):
            if free_since_timestamp:
                print(f"[{now.strftime('%H:%M:%S')}] {Colors.YELLOW}进入繁忙时段，已重置提醒计划。{Colors.ENDC}")
            free_since_timestamp = None
            scheduled_notification_time = None
            time.sleep(60)
            continue

        # 3. 进入空闲状态的逻辑
        # 如果刚从繁忙/锁定状态恢复
        if free_since_timestamp is None:
            free_since_timestamp = now
            print(f"[{now.strftime('%H:%M:%S')}] {Colors.CYAN}检测到空闲状态开始。正在计划下一次提醒...{Colors.ENDC}")
            
            # 使用韦伯分布生成一个等待时间 (分钟)
            wait_duration = WEIBULL_SCALE_MINUTES * np.random.weibull(WEIBULL_SHAPE)
            # 应用安全阈值，避免等待过久
            wait_duration = min(wait_duration, MAX_WAIT_MINUTES)
            
            scheduled_notification_time = now + timedelta(minutes=wait_duration)
            print(f"[{now.strftime('%H:%M:%S')}] {Colors.CYAN}根据韦伯分布，下一次提醒被安排在: {scheduled_notification_time.strftime('%H:%M:%S')} 左右。{Colors.ENDC}")
            
        # 4. 检查是否到达计划的提醒时间
        if scheduled_notification_time and now >= scheduled_notification_time:
            send_xiaoxi_notification()
            save_last_run_date()
            # 重置状态，等待明天
            free_since_timestamp = None
            scheduled_notification_time = None
        
        time.sleep(60)

if __name__ == "__main__":
    main()