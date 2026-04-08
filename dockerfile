# =========================
# AirPods Dockerfile (Full Project Copy)
# =========================

FROM rootfs_debootstrap:1.2.1



# -------------------------
# Set working directory for bootstrap
# -------------------------
WORKDIR /debug

# -------------------------
# Create non-root user early
# -------------------------
# Create bluetooth group if missing
RUN groupadd -r bluetooth || true && \
    useradd -ms /bin/bash airpods && \
    usermod -aG bluetooth airpods
# -------------------------
# Copy bootstrap files (system installer)
# -------------------------

COPY env.py /debug/env.py
# COPY debug.py /debug/debug.py
# COPY bootstrap.py /bootstrap.py
COPY requirements.txt /debug/requirements.txt
COPY filesystem.py /debug/filesystem.py




COPY filesystem.tar.gz /debug/filesystem.tar.gz

# -------------------------
# Run bootstrap to install Linux system and project root structure
# -------------------------
# RUN chmod +x /debug/bootstrap.py
# RUN python3 /debug/bootstrap.py

# -------------------------
# Run filesystem/sys.py to copy and arrange project files
# -------------------------

# RUN chmod +x /debug/filesystem.py
RUN python3 /debug/filesystem.py



# -------------------------
# Install Python dependencies
# -------------------------
RUN python3 -m pip install --no-cache-dir -r /debug/requirements.txt --break-system-packages

# -------------------------
# Run env.py to finalize environment, users, permissions, BLE capabilities
# -------------------------

# RUN chmod +x /debug/env.py
RUN python3 /debug/env.py

# COPY airpods_start.py /debug/airpods_start.py
# RUN chmod +x /debug/airpods_start.py
# -------------------------
# Ensure non-root user is default
# -------------------------

# RUN python3 bootstrap-destroy.py
# RUN python3 filesystem-destroy.py
USER airpods
# -------------------------
# Expose Web UI port
# -------------------------
EXPOSE 5000

# -------------------------
# Default startup command
# -------------------------
# Call the Python interpreter explicitly for your .py script
CMD ["python3", "/debug/airpods_start.py"]