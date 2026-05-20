FROM jenkins/jenkins:lts

USER root

# Update and install basic tools
RUN apt-get update && apt-get install -y \
    curl \
    python3 \
    python3-pip \
    python3-venv

# Install Docker CLI using the conventional script for robustness
RUN curl -fsSL https://get.docker.com -o get-docker.sh && sh get-docker.sh
# Note: This installs full docker engine usually, but we only need CLI. 
# It's a bit heavy but very reliable.
# Alternatively, use the binary download.

# Install Ansible via pip
# --break-system-packages is needed for newer Debian/Ubuntu in Python 3.11+ environment
RUN python3 -m pip install ansible requests --break-system-packages

# Clean up
RUN apt-get clean && rm -rf /var/lib/apt/lists/*

