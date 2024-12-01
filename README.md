# GPURegulator

GPURegulator is a Python-based system that monitors and regulates GPU usage. It provides features such as logging, configurable execution intervals, and dynamic GPU usage limits to ensure fair and efficient GPU allocation.

## Features

- **Monitor GPU usage**: Automatically kills processes exceeding a defined GPU memory threshold or GPU usage limit.
- **Configurable execution intervals**: Specify how often the script runs using a systemd timer.
- **Logging**: Records detailed logs of GPU activity and actions taken.
- **Log rotation**: Includes log rotation configuration to manage log size.

---

## Installation

### Prerequisites

- Python 3.x
- `nvidia-smi` available in the system path
- Systemd (for timer and service management)

### Steps to Install

1. Clone the repository and navigate to the project directory:
    ```
    git clone <repository-url>
    cd <repository-directory>
    ```

2. Install GPURegulator using the `make` command:
    ```
    sudo make install EXEC_INTERVAL=5min MAX_GPU_PER_USER=2 GPU_MEMORY_THRESHOLD_MB=2048
    ```

    - `EXEC_INTERVAL`: Interval at which the script is executed. Default is `5min`.
    - `MAX_GPU_PER_USER`: Maximum number of GPUs a user can use. Default is `2`.
    - `GPU_MEMORY_THRESHOLD_MB`: Maximum GPU memory in MB before killing processes. Default is `2048`.

3. Verify that the service and timer are active:
    ```
    systemctl status gpu-regulator.timer
    systemctl status gpu-regulator.service
    ```

---

## Usage

### Logging

Logs are stored in `/var/log/gpu_regulator.log`. You can view the logs with:
```
tail -f /var/log/gpu_regulator.log
```

### Log Rotation

Logs are rotated daily, with up to 7 compressed log files retained. The configuration is stored in `/etc/logrotate.d/gpu_regulator`.

---

## Uninstallation

To remove GPURegulator, run:
```
sudo make uninstall
```

This will:

- Stop and disable the systemd service and timer.
- Remove the script, logs, and related systemd files.

---

## Configuration

### Modify Execution Interval

To adjust the execution interval after installation, update the timer file:
```
sudo nano /etc/systemd/system/gpu-regulator.timer
```

Change the `OnUnitActiveSec` value, then reload the timer:
```
systemctl daemon-reload
systemctl restart gpu-regulator.timer
```

### Change GPU Limits or Thresholds

Update the service file to modify `MAX_GPU_PER_USER` or `GPU_MEMORY_THRESHOLD_MB`:
```
sudo nano /etc/systemd/system/gpu-regulator.service
```

Locate the `ExecStart` line and update the environment variables. For example:
```
ExecStart=/usr/bin/env MAX_GPU_PER_USER=3 GPU_MEMORY_THRESHOLD_MB=4096 /usr/bin/python3 /opt/gpu-regulator/gpu_regulator.py
```

Reload the service:
```
systemctl daemon-reload
systemctl restart gpu-regulator.service
```

---

## Development

### Testing Locally

Run the Python script directly for testing:
```
python3 /path/to/gpu_regulator.py
```

### Cleaning Up

To remove intermediate files or reset configurations:
```
make clean
```

---

## License

This project is licensed under the MIT License. See `LICENSE` for details.
