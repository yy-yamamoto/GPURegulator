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


def log(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")
    sys.stdout.flush()


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
                    user = ps_result.stdout.strip()
                    processes.append((gpu_uuid, pid, user))
        return processes
    except Exception as e:
        log(f"Error while fetching GPU processes: {e}")
        return []


def kill_gpu_processes(pid_list):
    try:
        for pid in pid_list:
            result = subprocess.run([KILL_PATH, pid], capture_output=True, text=True)
            if result.returncode == 0:
                log(f"Process {pid} has been killed.")
            else:
                log(f"Error: Failed to kill process {pid}.")
    except Exception as e:
        log(f"Error while killing processes: {e}")


def monitor_gpus():
    try:
        memory_threshold_mb = get_memory_threshold()
        max_gpu_per_user = get_max_gpu_per_user()
        # log(
        #     f"Monitoring GPUs with memory threshold: {memory_threshold_mb} MB and max GPUs per user: {max_gpu_per_user}"
        # )

        gpu_processes = get_gpu_processes(memory_threshold_mb)
        user_gpu_count = defaultdict(set)

        for gpu_uuid, pid, user in gpu_processes:
            user_gpu_count[user].add(gpu_uuid)

        for user, gpu_uuids in user_gpu_count.items():
            if len(gpu_uuids) > max_gpu_per_user:
                pid_list = [pid for _, pid, usr in gpu_processes if usr == user]
                log(f"Will kill processes for user {user}: {pid_list}")
                kill_gpu_processes(pid_list)
    except Exception as e:
        log(f"Unexpected error in monitor_gpus: {e}")


if __name__ == "__main__":
    try:
        monitor_gpus()
    except KeyboardInterrupt:
        log("Monitoring interrupted by user.")
    except Exception as e:
        log(f"Critical error: {e}")
