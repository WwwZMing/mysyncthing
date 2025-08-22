import time
import subprocess
from flask import Flask, request, jsonify

app = Flask(__name__)

# 服务端处理文件变更通知的全局变量
LAST_NOTIFIED_TIME = 0

# rsync 的源目录和目标目录。请根据你的实际情况进行修改。
# 示例：rsync -avz <source_dir> <destination_dir>
# <source_dir> 应该与你客户端监控的文件夹一致
# <destination_dir> 是 rsync 同步到的目标地址
RSYNC_SOURCE_DIR = "test/test_client/"
RSYNC_DESTINATION_DIR = "test/test_source"

@app.route('/')
def hello():
    return '<h1>欢迎来到我的 Web 服务！</h1><p>这是一个用于接收文件变更通知的服务。</p>'

@app.route('/notify', methods=['POST'])
def handle_notification():
    global LAST_NOTIFIED_TIME
    
    current_time = time.time()
    delay = 2
    # 检查与上一次通知的时间差是否小于10秒
    if current_time - LAST_NOTIFIED_TIME < delay:
        print(f"在{delay}秒内收到重复通知，忽略。")
        return jsonify({"message": "通知已成功接收，但因去抖动而被忽略"}), 200

    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "请求体必须是JSON格式"}), 400

        event_type = data.get('event')
        file_path = data.get('path')

        if not event_type or not file_path:
            return jsonify({"error": "缺少必要的参数: event 或 path"}), 400
        
        # 更新上一次通知的时间戳
        LAST_NOTIFIED_TIME = current_time

        print(f"收到新通知：事件类型: {event_type}, 文件路径: {file_path}")
        if event_type == "created" or event_type == "modified":
            # 触发 rsync 同步
            trigger_rsync_changed()
        elif event_type == "deleted":
            # 触发 rsync 删除同步
            trigger_rsync_delete()
        else:
            return jsonify({"error": "未知事件类型"}), 400
        
        return jsonify({"message": "通知已成功接收并已触发同步"}), 200

    except Exception as e:
        print(f"处理通知时发生错误: {e}")
        return jsonify({"error": "服务器内部错误"}), 500

def trigger_rsync_changed():
    """执行 rsync 命令来同步文件夹。"""
    print("正在触发 rsync 同步...")
    try:
        # 使用 subprocess.run 执行命令，这是推荐的写法
        # 将命令和参数作为列表传递，可以防止注入攻击
        result = subprocess.run(
            ["rsync", "-avz", RSYNC_SOURCE_DIR, RSYNC_DESTINATION_DIR],
            check=True, # 如果命令失败（返回非0状态码），则抛出异常
            capture_output=True,
            text=True
        )
        print("rsync 同步成功！")
        print("rsync 输出：\n", result.stdout)
    except FileNotFoundError:
        print("错误：rsync 命令未找到。请确保 rsync 已安装并位于 PATH 中。")
    except subprocess.CalledProcessError as e:
        print(f"rsync 同步失败，返回码：{e.returncode}")
        print("rsync 错误输出：\n", e.stderr)
    except Exception as e:
        print(f"执行 rsync 时发生未知错误：{e}")

def trigger_rsync_delete():
    """执行 rsync 命令来同步文件夹。"""
    print("正在触发 rsync 同步...")
    try:
        # 使用 subprocess.run 执行命令，这是推荐的写法
        # 将命令和参数作为列表传递，可以防止注入攻击
        result = subprocess.run(
            ["rsync", "-avz", "--delete", RSYNC_SOURCE_DIR, RSYNC_DESTINATION_DIR],
            check=True, # 如果命令失败（返回非0状态码），则抛出异常
            text=True
        )
        print("rsync 同步成功！")
    except FileNotFoundError:
        print("错误：rsync 命令未找到。请确保 rsync 已安装并位于 PATH 中。")
    except subprocess.CalledProcessError as e:
        print(f"rsync 同步失败，返回码：{e.returncode}")
        print("rsync 错误输出：\n", e.stderr)
    except Exception as e:
        print(f"执行 rsync 时发生未知错误：{e}")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=18384)