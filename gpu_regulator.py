import os
import subprocess
import sys
from collections import defaultdict
from datetime import datetime

# デフォルトのメモリ閾値（MB単位）と使用可能GPU台数
DEFAULT_MEMORY_THRESHOLD_MB = 2048
DEFAULT_MAX_GPU_PER_USER = 2

# NVIDIA-SMIとpsのフルパスを設定
NVIDIA_SMI_PATH = "/usr/bin/nvidia-smi"
PS_PATH = "/usr/bin/ps"
KILL_PATH = "/bin/kill"


def get_memory_threshold():
    return int(os.getenv("GPU_MEMORY_THRESHOLD_MB", DEFAULT_MEMORY_THRESHOLD_MB))


def get_max_gpu_per_user():
    return int(os.getenv("MAX_GPU_PER_USER", DEFAULT_MAX_GPU_PER_USER))


def normalize_username(username):
    """ ユーザー名を '-' で分割し、最も長い部分を返す """
    return max(username.split("-"), key=len)


def log(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")
    sys.stdout.flush()


def get_process_start_time(pid):
    """ 指定したプロセスIDの開始時刻を取得 """
    try:
        result = subprocess.run(
            ["env", "LC_TIME=C", PS_PATH, "-o", "lstart=", "-p", pid],
            capture_output=True,
            text=True
        )
        if result.returncode == 0 and result.stdout.strip():
            start_time = datetime.strptime(result.stdout.strip(), "%a %b %d %H:%M:%S %Y")
            return start_time
    except Exception as e:
        log(f"Error while fetching process start time for PID {pid}: {e}")
    return None


def get_gpu_processes(memory_threshold_mb):
    try:
        result = subprocess.run(
            [
                NVIDIA_SMI_PATH,
                "--query-compute-apps=gpu_uuid,pid,used_gpu_memory",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            log("Error: Unable to fetch GPU information.")
            return []

        processes = []
        for line in result.stdout.strip().split("\n"):
            if line:
                gpu_uuid, pid, used_memory = map(str.strip, line.split(","))
                used_memory_mb = int(used_memory)
                if used_memory_mb <= memory_threshold_mb:
                    continue
                ps_result = subprocess.run(
                    [PS_PATH, "-o", "user=", "-p", pid], capture_output=True, text=True
                )
                if ps_result.returncode == 0 and ps_result.stdout.strip():
                    user = normalize_username(ps_result.stdout.strip())  # ユーザー名を正規化
                    start_time = get_process_start_time(pid)
                    if start_time:
                        processes.append((gpu_uuid, pid, user, start_time))
        return processes
    except Exception as e:
        log(f"Error while fetching GPU processes: {e}")
        return []


def kill_gpu_process(pid):
    """ 指定したプロセスをKill """
    try:
        result = subprocess.run([KILL_PATH, pid], capture_output=True, text=True)
        if result.returncode == 0:
            log(f"Process {pid} has been killed.")
        else:
            log(f"Error: Failed to kill process {pid}.")
    except Exception as e:
        log(f"Error while killing process {pid}: {e}")


def monitor_gpus():
    try:
        memory_threshold_mb = get_memory_threshold()
        max_gpu_per_user = get_max_gpu_per_user()

        gpu_processes = get_gpu_processes(memory_threshold_mb)
        user_gpu_usage = defaultdict(lambda: defaultdict(list))

        # ユーザーごとのGPUプロセスを管理
        for gpu_uuid, pid, user, start_time in gpu_processes:
            user_gpu_usage[user][gpu_uuid].append((pid, start_time))

        for user, gpu_data in user_gpu_usage.items():
            total_gpus = len(gpu_data)
            if total_gpus > max_gpu_per_user:
                log(f"User {user} exceeds GPU limit ({total_gpus} > {max_gpu_per_user})")

                excess_gpus = total_gpus - max_gpu_per_user

                # GPUごとにプロセスを新しい順にソートし、超過分を削除
                sorted_gpu_list = sorted(gpu_data.items(), key=lambda x: min(p[1] for p in x[1]))

                for gpu_uuid, processes in sorted_gpu_list[:excess_gpus]:
                    processes.sort(key=lambda x: x[1], reverse=True)  # 開始時間が新しい順
                    pid_to_kill, _ = processes[0]  # 最新のプロセスを停止
                    log(f"Killing process {pid_to_kill} for user {user} on GPU {gpu_uuid}")
                    kill_gpu_process(pid_to_kill)

    except Exception as e:
        log(f"Unexpected error in monitor_gpus: {e}")


if __name__ == "__main__":
    try:
        monitor_gpus()
    except KeyboardInterrupt:
        log("Monitoring interrupted by user.")
    except Exception as e:
        log(f"Critical error: {e}")
