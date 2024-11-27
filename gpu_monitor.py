import subprocess
from collections import defaultdict
from datetime import datetime
import os

# デフォルトのメモリ閾値（MB単位）
DEFAULT_MEMORY_THRESHOLD_MB = 2048

def get_memory_threshold():
    # 環境変数からメモリ閾値を取得、未設定の場合はデフォルト値を使用
    return int(os.getenv("GPU_MEMORY_THRESHOLD_MB", DEFAULT_MEMORY_THRESHOLD_MB))

def log(message):
    # 現在の日付と時間を含めたログ出力
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def get_gpu_processes(memory_threshold_mb):
    # NVIDIA-SMIコマンドを使用してGPUのプロセス情報を取得
    result = subprocess.run(
        ['nvidia-smi', '--query-compute-apps=gpu_uuid,pid,used_gpu_memory', '--format=csv,noheader,nounits'],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        log("Error: Unable to fetch GPU information.")
        return []

    processes = []
    for line in result.stdout.strip().split('\n'):
        if line:
            gpu_uuid, pid, used_memory = map(str.strip, line.split(','))
            used_memory_mb = int(used_memory)  # メモリ使用量をMB単位で取得
            if used_memory_mb <= memory_threshold_mb:  # 閾値以下のプロセスをスキップ
                continue
            # psコマンドでプロセスIDからユーザー名を取得
            ps_result = subprocess.run(['ps', '-o', 'user=', '-p', pid], capture_output=True, text=True)
            if ps_result.returncode == 0 and ps_result.stdout.strip():
                user = ps_result.stdout.strip()
                processes.append((gpu_uuid, pid, user))
    return processes

def kill_gpu_processes(pid_list):
    # PIDリストに基づいてプロセスをKill
    for pid in pid_list:
        result = subprocess.run(['kill', pid], capture_output=True, text=True)
        if result.returncode == 0:
            log(f"Process {pid} has been killed.")
        else:
            log(f"Error: Failed to kill process {pid}.")

def monitor_gpus():
    # メモリ閾値を取得
    memory_threshold_mb = get_memory_threshold()
    # log(f"Monitoring GPUs with memory threshold: {memory_threshold_mb} MB")

    # GPUプロセスを取得
    gpu_processes = get_gpu_processes(memory_threshold_mb)

    # ユーザーとGPU UUIDごとのプロセス情報をカウント
    user_gpu_count = defaultdict(set)
    for gpu_uuid, pid, user in gpu_processes:
        user_gpu_count[user].add(gpu_uuid)

    # 条件に合うユーザーのGPUプロセスをKill
    for user, gpu_uuids in user_gpu_count.items():
        if len(gpu_uuids) >= 3:
            pid_list = [pid for _, pid, usr in gpu_processes if usr == user]
            log(f"Will kill processes for user {user}: {pid_list}")
            kill_gpu_processes(pid_list)

if __name__ == "__main__":
    monitor_gpus()
