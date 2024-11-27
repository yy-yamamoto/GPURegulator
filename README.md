# GPU MANNERS

A program that manages the number of GPUs in use

## Usage

```shell
sudo crontab -e
```

Add the following code.

```shell
*/5 * * * * /usr/bin/python3 /home/"root"/gpu_manners/gpu_monitor.py >> /var/log/gpu_manners.log 2>&1
```

Note that you need to replace "root" with your own root directory

## Parameters

GPU_MEMORY_THRESHOLD_MB: Minimum GPU memory usage to be considered as using a GPU

### How to change the parameters

```
export GPU_MEMORY_THRESHOLD_MB=512
python script.py
```
