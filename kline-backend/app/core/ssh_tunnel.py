"""SSH隧道管理模块"""
import subprocess
import time
from contextlib import contextmanager
from app.core.config import settings


class SSHTunnelManager:
    """SSH隧道管理器"""

    def __init__(self):
        self.ssh_host = settings.SSH_HOST
        self.local_port = settings.SSH_LOCAL_PORT
        self.remote_port = settings.SSH_REMOTE_PORT
        self.process = None

    def start(self):
        """启动SSH隧道"""
        if self.is_alive():
            print(f"SSH隧道已经在运行")
            return

        cmd = [
            'ssh', '-N', '-L',
            f'{self.local_port}:localhost:{self.remote_port}',
            self.ssh_host
        ]

        print(f"正在创建SSH隧道: {self.ssh_host}:{self.remote_port} -> localhost:{self.local_port}")
        self.process = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        time.sleep(2)  # 等待隧道建立
        print(f"SSH隧道已建立")

    def stop(self):
        """关闭SSH隧道"""
        if self.process:
            self.process.terminate()
            self.process.wait()
            self.process = None
            print("SSH隧道已关闭")

    def is_alive(self):
        """检查隧道是否存活"""
        return self.process and self.process.poll() is None

    def restart(self):
        """重启SSH隧道"""
        self.stop()
        time.sleep(1)
        self.start()

    @contextmanager
    def tunnel(self):
        """上下文管理器"""
        self.start()
        try:
            yield
        finally:
            self.stop()


# 全局单例
tunnel_manager = SSHTunnelManager()
