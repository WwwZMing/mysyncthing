import time
import requests
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# 服务端地址和端口
SERVER_URL = "http://localhost:18384"
API_ENDPOINT = "/notify"

# 新增：用于去抖动的字典，记录每个路径的最后修改时间
last_created_time = {}
last_removed_time = {}
DEBOUNCE_DELAY = 5 # 去抖动延迟，单位秒

def send_notification(event_type, file_path):
    """向服务端发送通知"""
    try:
        response = requests.post(f"{SERVER_URL}{API_ENDPOINT}", json={"event": event_type, "path": file_path})
        response.raise_for_status()
        print("Notification sent successfully to server.")
    except requests.exceptions.RequestException as e:
        print(f"Failed to send notification: {e}")

class MyHandler(FileSystemEventHandler):
    def on_created(self, event):
        """当文件被新增时调用"""
        if not event.is_directory:
            dir_path = os.path.dirname(event.src_path)
            if(self.debounce_event(last_removed_time, dir_path, DEBOUNCE_DELAY)):
                return

            print(f"File created: {event.src_path}")
            send_notification("created", event.src_path)

        if event.is_directory:
            # 对于目录创建事件，直接发送通知
            print(f"Directory created: {event.src_path}")
            send_notification("created", event.src_path)

    def on_deleted(self, event):
        """当文件被删除时调用"""
        if not event.is_directory:
            dir_path = os.path.dirname(event.src_path)
            if(self.debounce_event(last_removed_time, dir_path, DEBOUNCE_DELAY)):
                return

            print(f"File deleted: {event.src_path}")
            send_notification("deleted", event.src_path)
        if event.is_directory:
            # 对于目录删除事件，直接发送通知
            print(f"Directory deleted: {event.src_path}")
            send_notification("deleted", event.src_path)

    def on_modified(self, event):
        """当文件被修改时调用"""
        send_notification("modified", event.src_path)

    
    def debounce_event(self, event_time_map: map, key: object, delay: int) -> bool:
        """去抖动处理，避免短时间内重复触发事件"""
        """检查是否在指定延迟内已经处理过该事件"""
        current_time = time.time()
        if key in event_time_map and current_time - event_time_map[key] < delay:
            print(f"在 {DEBOUNCE_DELAY} 秒内收到 {key} 的重复事件，忽略。")
            return True  # 应该被忽略
        event_time_map[key] = current_time
        return False # 应该被处理
    

if __name__ == "__main__":
    # 新增：os模块用于处理路径
    import os
    
    path_to_watch = "test/test_client" # 替换成你要监控的文件夹路径
    event_handler = MyHandler()
    observer = Observer()
    observer.schedule(event_handler, path_to_watch, recursive=True)
    observer.start()

    print(f"Watching for changes in: {path_to_watch}")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()