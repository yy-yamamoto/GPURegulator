# Variables
INSTALL_DIR = /opt/gpu-regulator
SERVICE_DIR = /etc/systemd/system
LOG_DIR = /var/log
LOG_FILE = $(LOG_DIR)/gpu_regulator.log
LOGROTATE_DIR = /etc/logrotate.d
LOGROTATE_FILE = $(LOGROTATE_DIR)/gpu_regulator
PYTHON_SCRIPT = gpu_regulator.py
SERVICE_FILE = gpu-regulator.service
TIMER_FILE = gpu-regulator.timer

# GPU Configuration
MAX_GPU_PER_USER ?= 2
GPU_MEMORY_THRESHOLD_MB ?= 2048
EXEC_INTERVAL ?= 5min  # デフォルトの実行間隔

.PHONY: all install uninstall clean

all:
	@echo "Run 'make install' to install GPURegulator."

install:
	@echo "Installing GPURegulator..."
	# Create installation directory
	mkdir -p $(INSTALL_DIR)
	cp $(PYTHON_SCRIPT) $(INSTALL_DIR)/
	chmod +x $(INSTALL_DIR)/$(PYTHON_SCRIPT)
	# Create log file and set permissions
	mkdir -p $(LOG_DIR)
	touch $(LOG_FILE)
	chmod 644 $(LOG_FILE)
	# Create logrotate configuration
	mkdir -p $(LOGROTATE_DIR)
	echo "/var/log/gpu_regulator.log {" > $(LOGROTATE_FILE)
	echo "    daily" >> $(LOGROTATE_FILE)
	echo "    rotate 7" >> $(LOGROTATE_FILE)
	echo "    compress" >> $(LOGROTATE_FILE)
	echo "    missingok" >> $(LOGROTATE_FILE)
	echo "    notifempty" >> $(LOGROTATE_FILE)
	echo "    create 644 root root" >> $(LOGROTATE_FILE)
	echo "    postrotate" >> $(LOGROTATE_FILE)
	echo "        systemctl restart gpu-regulator.timer" >> $(LOGROTATE_FILE)
	echo "    endscript" >> $(LOGROTATE_FILE)
	echo "}" >> $(LOGROTATE_FILE)
	# Update service file with logging configuration
	sed -i "s|ExecStart=.*|ExecStart=/usr/bin/env MAX_GPU_PER_USER=$(MAX_GPU_PER_USER) GPU_MEMORY_THRESHOLD_MB=$(GPU_MEMORY_THRESHOLD_MB) /usr/bin/python3 $(INSTALL_DIR)/$(PYTHON_SCRIPT)|" $(SERVICE_FILE)
	sed -i "/\[Service\]/a StandardOutput=append:$(LOG_FILE)" $(SERVICE_FILE)
	sed -i "/\[Service\]/a StandardError=append:$(LOG_FILE)" $(SERVICE_FILE)
	# Update timer file with execution interval
	sed -i "s|OnUnitActiveSec=.*|OnUnitActiveSec=$(EXEC_INTERVAL)|" $(TIMER_FILE)
	# Install systemd service and timer
	cp $(SERVICE_FILE) $(SERVICE_DIR)/
	cp $(TIMER_FILE) $(SERVICE_DIR)/
	systemctl daemon-reload
	systemctl enable $(SERVICE_FILE)
	systemctl start $(SERVICE_FILE)
	systemctl enable $(TIMER_FILE)
	systemctl start $(TIMER_FILE)
	@echo "Installation complete."

uninstall:
	@echo "Uninstalling GPURegulator..."
	# Stop and disable the timer
	systemctl stop $(TIMER_FILE)
	systemctl disable $(TIMER_FILE)
	# Stop and disable the service
	systemctl stop $(SERVICE_FILE)
	systemctl disable $(SERVICE_FILE)
	# Remove installed files
	rm -rf $(INSTALL_DIR)
	rm -f $(SERVICE_DIR)/$(SERVICE_FILE)
	rm -f $(SERVICE_DIR)/$(TIMER_FILE)
	rm -f $(LOG_FILE)
	rm -f $(LOGROTATE_FILE)
	# Reload systemd
	systemctl daemon-reload
	@echo "Uninstallation complete."

clean:
	@echo "Nothing to clean."
