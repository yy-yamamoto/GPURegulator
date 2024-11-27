import subprocess
from collections import defaultdict

def get_gpu_processes():
    # NVIDIA-SMIコマンドを使用してGPUのプロセス情報を取得
    result = subprocess.run(['nvidia-smi', '--query-compute-apps=gpu_uuid,pid,used_gpu_memory', '--format=csv,noheader'], capture_output=True, text=True)
    if result.returncode != 0:
        print("Error: Unable to fetch GPU information.")
        return []

    processes = []
    for line in result.stdout.strip().split('\n'):
        if line:
            gpu_uuid, pid, _ = map(str.strip, line.split(','))
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
            print(f"Process {pid} has been killed.")
        else:
            print(f"Error: Failed to kill process {pid}.")

def monitor_gpus():
    # GPUプロセスを取得
    gpu_processes = get_gpu_processes()

    # ユーザーとGPU UUIDごとのプロセス情報をカウント
    user_gpu_count = defaultdict(set)
    for gpu_uuid, pid, user in gpu_processes:
        user_gpu_count[user].add(gpu_uuid)

    # 条件に合うユーザーのGPUプロセスをKill
    for user, gpu_uuids in user_gpu_count.items():

        # print(f"{user}: {gpu_uuids}, used {len(gpu_uuids)}")
        if len(gpu_uuids) >= 3:
            pid_list = [pid for _, pid, usr in gpu_processes if usr == user]
            print(f"will kill {user}, {pid_list}")
            kill_gpu_processes(pid_list)


if __name__ == "__main__":
    monitor_gpus()
