import time
import json
import datetime
from winotify import Notification, Notifier
import ctypes
import numpy as np
import os
import sys

# --- 全局配置 ---
SCHEDULE_FILE = 'schedule.jsonl'
LAST_DATE_FILE = 'last_notification_date.txt'
problems_file = 'problems.json'
progress_file = 'progress.json'
CHECK_INTERVAL_SECONDS = 15  # 检查用户状态的频率
IDLE_THRESHOLD_SECONDS = 300  # 5分钟无操作视为进入空闲状态

# 韦伯分布参数 (塑造提醒“性格”)
WEIBULL_SHAPE = 2.0  # k > 1 表示“空闲越久，越可能提醒”
WEIBULL_SCALE_MINUTES = 90.0  # λ, 平均提醒间隔

# --- 角色化内容 ---
XIAOXI_LOGO = r"""
   ____            U  ___ u  _   _                  __  __   __  __
U /"___|u   ___     \/"_ \/ | \ |"|       ___       \ \/"/   \ \/"/
\| |  _ /  |_"_|    | | | |<|  \| |>     |_"_|      /\  /\   /\  /\
 | |_| |    | | .-,_| |_| |U| |\  |u      | |      U /  \ u U /  \ u
  \____|  U/| |\u\_)-\___/  |_| \_|     U/| |\u     /_/\_\   /_/\_\
  _)(|_.-,_|___|_,-.  \\    ||   \\,-.-,_|___|_,-.,-,>> \\_,-,>> \\_
 (__)__)\_)-' '-(_/  (__)   (_")  (_/ \_)-' '-(_/  \_)  (__)\_)  (__) 
"""
messages = [
    "你的进度有点慢，今天研究一下这个问题",
    "我刚才想到了一个算法上的优化点，记下来，有空看看",
    "不要松懈，保持思考的习惯",
    "基础不牢，地动山摇，复习一下这个知识点",
    "这张知识图谱对你的学习有帮助"
]
notifier = Notifier(
    app_id="SillyTavern Immersive Task Assistant",
    icon=os.path.join(os.path.dirname(sys.argv[0]), 'icon.png'),
    threaded=True
)

# --- 核心功能函数 ---

class LASTINPUTINFO(ctypes.Structure):
    _fields_ = [
        ('cbSize', ctypes.c_uint),
        ('dwTime', ctypes.c_uint),
    ]

def get_idle_duration():
    lastInputInfo = LASTINPUTINFO()
    lastInputInfo.cbSize = ctypes.sizeof(lastInputInfo)
    ctypes.windll.user32.GetLastInputInfo(ctypes.byref(lastInputInfo))
    millis = ctypes.windll.kernel32.GetTickCount() - lastInputInfo.dwTime
    return millis / 1000.0

def load_schedule():
    try:
        with open(SCHEDULE_FILE, 'r', encoding='utf-8') as f:
            return [json.loads(line) for line in f]
    except FileNotFoundError:
        print(f"错误: 未找到课程表文件 '{SCHEDULE_FILE}'。")
        return []

def is_in_class(now, schedule):
    today_str = now.strftime('%Y-%m-%d')
    for entry in schedule:
        if entry['date'] == today_str:
            for period in entry['periods']:
                start_time = datetime.datetime.strptime(f"{today_str} {period['start']}", '%Y-%m-%d %H:%M').time()
                end_time = datetime.datetime.strptime(f"{today_str} {period['end']}", '%Y-%m-%d %H:%M').time()
                if start_time <= now.time() <= end_time:
                    return True
    return False

def get_next_task_title():
    try:
        with open(problems_file, 'r', encoding='utf-8') as f:
            problems = json.load(f)
        
        if not os.path.exists(progress_file):
            return problems[0]['title'] if problems else "新任务"

        with open(progress_file, 'r', encoding='utf-8') as f:
            progress = json.load(f)
        
        completed_ids = set(progress.get('completed_ids', []))
        
        for problem in problems:
            if problem['id'] not in completed_ids:
                return problem['title']
        return "所有任务已完成"
    except Exception:
        return "新任务"

def send_notification():
    today_str = datetime.date.today().isoformat()
    task_title = get_next_task_title()
    message = np.random.choice(messages)
    
    toast = Notification(
        title="林教授的每日提醒",
        msg=f"{message}\n今天的任务是: “{task_title}”",
        duration="long"
    )
    
    if notifier.show(toast):
        try:
            with open(LAST_DATE_FILE, 'w') as f:
                f.write(today_str)
            print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 提醒发送成功，并已记录日期。")
        except Exception as e:
            print(f"错误: 无法写入上次通知日期文件: {e}")

# <<< FIX START: 新增的“每日一次”检查函数 >>>
def has_notified_today():
    """检查今天是否已经成功发送过通知"""
    try:
        with open(LAST_DATE_FILE, 'r') as f:
            last_date_str = f.read().strip()
        today_str = datetime.date.today().isoformat()
        return last_date_str == today_str
    except FileNotFoundError:
        # 如果文件不存在，说明从未发送过，可以发送
        return False
    except Exception as e:
        print(f"警告: 无法读取上次通知日期文件: {e}。将按未通知处理。")
        return False
# <<< FIX END >>>

def main_monitoring_loop():
    print("监控已开始，等待空闲时机...")
    last_active_time = time.time()
    next_notification_time = None
    is_planning = False

    while True:
        now = datetime.datetime.now()
        
        # <<< FIX START: 将“每日一次”检查作为最高优先级 >>>
        if has_notified_today():
            # 如果今天已经提醒过，则无需再进行任何检查，大幅降低资源占用
            # 直接休眠10分钟，然后进入下一个循环，再次检查日期
            time.sleep(600) 
            continue # 跳过本次循环的后续所有逻辑
        # <<< FIX END >>>

        if get_idle_duration() < CHECK_INTERVAL_SECONDS: # 用户正在活跃
            if is_planning:
                print(f"[{now.strftime('%H:%M:%S')}] 用户已恢复活跃，取消提醒计划。")
                next_notification_time = None
                is_planning = False
            last_active_time = time.time()
        else: # 用户处于空闲状态
            idle_duration = time.time() - last_active_time
            if idle_duration > IDLE_THRESHOLD_SECONDS and not is_planning:
                if not is_in_class(now, load_schedule()):
                    print(f"[{now.strftime('%H:%M:%S')}] 检测到空闲状态开始。正在计划下一次提醒...")
                    # 使用韦伯分布计算下一次提醒的延迟时间
                    delay_minutes = np.random.weibull(WEIBULL_SHAPE) * WEIBULL_SCALE_MINUTES
                    delay_seconds = delay_minutes * 60
                    next_notification_time = now + datetime.timedelta(seconds=delay_seconds)
                    is_planning = True
                    print(f"[{now.strftime('%H:%M:%S')}] 根据韦伯分布，下一次提醒被安排在: {next_notification_time.strftime('%H:%M:%S')} 左右。")

        if is_planning and now >= next_notification_time:
            print(f"[{now.strftime('%H:%M:%S')}] 到达计划时间，正在发送提醒...")
            send_notification()
            # 重置状态，避免重复发送
            next_notification_time = None
            is_planning = False
            # 发送成功后，has_notified_today()将在下一个循环中返回True，从而进入长时休眠

        time.sleep(CHECK_INTERVAL_SECONDS)

if __name__ == "__main__":
    print(XIAOXI_LOGO)
    print("======================================================")
    print("林教授的每日提醒脚本已启动 (智能韦伯调度模式)...")
    
    # 检查icon.png是否存在
    icon_path = os.path.join(os.path.dirname(sys.argv[0]), 'icon.png')
    if not os.path.exists(icon_path):
        print("警告: 未在脚本目录找到 icon.png 文件，通知可能不显示图标。")
        
    print(f"课程表加载成功，共 {len(load_schedule())} 天的计划。")
    print("本窗口将在 3 秒后自动开始后台监控。")
    print("======================================================")
    time.sleep(3)
    main_monitoring_loop()