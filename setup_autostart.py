import os
import sys
import shutil
import win32com.client

def get_python_path():
    """
    自动查找当前 Python 可执行文件路径
    """
    return sys.executable

def create_shortcut(target, shortcut_name, start_in, arguments=""):
    """
    创建 Windows 快捷方式
    """
    shell = win32com.client.Dispatch("WScript.Shell")
    startup_path = os.path.join(os.getenv("APPDATA"), r"Microsoft\Windows\Start Menu\Programs\Startup")
    shortcut_path = os.path.join(startup_path, f"{shortcut_name}.lnk")

    shortcut = shell.CreateShortcut(shortcut_path)
    shortcut.TargetPath = target
    shortcut.Arguments = arguments
    shortcut.WorkingDirectory = start_in
    shortcut.IconLocation = target
    shortcut.Save()

    print(f"[√] 已创建开机启动项: {shortcut_path}")

def main():
    python_path = get_python_path()
    project_dir = os.path.dirname(os.path.abspath(__file__))
    notifier_path = os.path.join(project_dir, "notifier.py")

    if not os.path.exists(notifier_path):
        print("[×] 错误: 未找到 notifier.py，请确认该脚本在项目目录中。")
        return

    # 快捷方式名称
    shortcut_name = "SillyTavern Notifier"

    # 参数格式: "notifier.py"
    create_shortcut(
        target=python_path,
        shortcut_name=shortcut_name,
        start_in=project_dir,
        arguments=f"\"{notifier_path}\""
    )

    print("[√] 开机自启配置完成！请重启电脑测试效果。")

if __name__ == "__main__":
    main()
