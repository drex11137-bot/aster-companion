# syntax=docker/dockerfile:1
ARG UBUNTU_VERSION=24.04
FROM ubuntu:${UBUNTU_VERSION} AS base

LABEL maintainer="Antigravity Autonomous Engineering Team"
LABEL description="Reproducible Multi-Domain Engineering Workstation (Ubuntu 24.04 LTS)"
LABEL version="1.0.0"

# Set environment variables for non-interactive builds
ENV DEBIAN_FRONTEND=noninteractive \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    TZ=UTC \
    ANDROID_HOME=/usr/local/android-sdk \
    ANDROID_SDK_ROOT=/usr/local/android-sdk \
    GHIDRA_HOME=/usr/local/ghidra \
    CODEQL_HOME=/usr/local/codeql \
    JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64 \
    PATH=/usr/local/android-sdk/cmdline-tools/latest/bin:/usr/local/android-sdk/platform-tools:/usr/local/android-sdk/build-tools/34.0.0:/usr/local/ghidra/support:/usr/local/codeql:/usr/local/jadx/bin:/workspaces/codespaces-blank/tools/scripts:/home/codespace/.local/bin:/home/codespace/.gemini/antigravity-cli/bin:${PATH}

# 1. Create codespace user with sudo permissions
RUN groupadd --gid 1000 codespace \
    && useradd --uid 1000 --gid 1000 -m -s /bin/bash codespace \
    && apt-get update \
    && apt-get install -y --no-install-recommends sudo ca-certificates curl gnupg lsb-release \
    && echo "codespace ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/codespace \
    && chmod 0440 /etc/sudoers.d/codespace \
    && rm -rf /var/lib/apt/lists/*

# 2. Install Core System, C/C++ Toolchain, CLI Utilities, Java, Network & Forensics tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Core Build & Compilers
    build-essential \
    gcc \
    g++ \
    clang \
    clang-tools \
    llvm \
    lld \
    lldb \
    gdb \
    gdb-multiarch \
    binutils \
    patchelf \
    upx-ucl \
    cmake \
    ninja-build \
    pkg-config \
    make \
    autoconf \
    automake \
    libtool \
    checksec \
    # CLI Utilities
    git \
    gh \
    wget \
    jq \
    ripgrep \
    fd-find \
    fzf \
    tree \
    zip \
    unzip \
    tar \
    xz-utils \
    zstd \
    p7zip-full \
    file \
    software-properties-common \
    less \
    nano \
    vim \
    procps \
    strace \
    ltrace \
    net-tools \
    iproute2 \
    dnsutils \
    bsdmainutils \
    # Java JDKs
    openjdk-17-jdk \
    openjdk-21-jdk \
    # Python & Pip
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    pipx \
    # Reverse Engineering & Binary Tools
    radare2 \
    yara \
    wabt \
    # Network Forensics (wireshark non-interactive pre-seed)
    nmap \
    tcpdump \
    tshark \
    wireshark-common \
    libcap2-bin \
    && rm -rf /var/lib/apt/lists/* \
    && ln -s /usr/bin/fdfind /usr/local/bin/fd || true

# 3. Setup Node.js 22 LTS, npm, yarn, pnpm & Playwright
RUN curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && apt-get update && apt-get install -y --no-install-recommends nodejs \
    && npm install -g npm@latest corepack pnpm yarn @stoplight/spectral-cli \
    && corepack enable \
    && rm -rf /var/lib/apt/lists/*

# 4. Install Python Security, Binary Analysis & Testing Packages
RUN pip3 install --no-cache-dir --break-system-packages \
    semgrep \
    bandit \
    pip-audit \
    frida-tools \
    pwntools \
    scapy \
    yara-python \
    playwright \
    pytest \
    pytest-xdist \
    requests \
    pyyaml \
    rich

# 5. Create Tool Directories with Proper Ownership
RUN mkdir -p /usr/local/android-sdk/cmdline-tools \
             /usr/local/ghidra \
             /usr/local/codeql \
             /usr/local/jadx \
             /workspaces \
             /home/codespace/.local/bin \
    && chown -R codespace:codespace /usr/local/android-sdk \
                                   /usr/local/ghidra \
                                   /usr/local/codeql \
                                   /usr/local/jadx \
                                   /workspaces \
                                   /home/codespace

# 6. Install Android Command-Line Tools & SDK components
RUN curl -fsSL https://dl.google.com/android/repository/commandlinetools-linux-11076708_latest.zip -o /tmp/cmdline-tools.zip \
    && unzip -q /tmp/cmdline-tools.zip -d /tmp/cmdline-tools-extracted \
    && mkdir -p /usr/local/android-sdk/cmdline-tools/latest \
    && mv /tmp/cmdline-tools-extracted/cmdline-tools/* /usr/local/android-sdk/cmdline-tools/latest/ \
    && rm -rf /tmp/cmdline-tools* \
    && yes | /usr/local/android-sdk/cmdline-tools/latest/bin/sdkmanager --licenses || true \
    && /usr/local/android-sdk/cmdline-tools/latest/bin/sdkmanager --install \
       "platform-tools" \
       "build-tools;34.0.0" \
       "platforms;android-34" || true \
    && chown -R codespace:codespace /usr/local/android-sdk

# 7. Install APKTool, JADX & Smali/Baksmali
RUN curl -fsSL https://raw.githubusercontent.com/iBotPeaches/Apktool/master/scripts/linux/apktool -o /usr/local/bin/apktool \
    && curl -fsSL https://github.com/iBotPeaches/Apktool/releases/download/v2.10.0/apktool_2.10.0.jar -o /usr/local/bin/apktool.jar \
    && chmod +x /usr/local/bin/apktool /usr/local/bin/apktool.jar \
    && curl -fsSL https://github.com/skylot/jadx/releases/download/v1.5.0/jadx-1.5.0.zip -o /tmp/jadx.zip \
    && unzip -q /tmp/jadx.zip -d /usr/local/jadx \
    && ln -s /usr/local/jadx/bin/jadx /usr/local/bin/jadx \
    && ln -s /usr/local/jadx/bin/jadx-gui /usr/local/bin/jadx-gui \
    && rm -f /tmp/jadx.zip \
    && chown -R codespace:codespace /usr/local/jadx

# 8. Install Ghidra Headless
RUN GHIDRA_VER="11.2.1" \
    && GHIDRA_DATE="20241105" \
    && curl -fsSL "https://github.com/NationalSecurityAgency/ghidra/releases/download/Ghidra_${GHIDRA_VER}_build/ghidra_${GHIDRA_VER}_PUBLIC_${GHIDRA_DATE}.zip" -o /tmp/ghidra.zip \
    && unzip -q /tmp/ghidra.zip -d /tmp/ghidra_extracted \
    && mv /tmp/ghidra_extracted/ghidra_*/* /usr/local/ghidra/ \
    && rm -rf /tmp/ghidra* \
    && chown -R codespace:codespace /usr/local/ghidra

# 9. Install Security Scanners (Trivy, Gitleaks, OSV-Scanner, CodeQL CLI)
RUN curl -fsSL https://github.com/aquasecurity/trivy/releases/download/v0.58.2/trivy_0.58.2_Linux-64bit.tar.gz | tar -xz -C /usr/local/bin trivy \
    && chmod +x /usr/local/bin/trivy \
    && curl -fsSL https://github.com/gitleaks/gitleaks/releases/download/v8.21.2/gitleaks_8.21.2_linux_x64.tar.gz | tar -xz -C /usr/local/bin gitleaks \
    && chmod +x /usr/local/bin/gitleaks \
    && curl -fsSL https://github.com/google/osv-scanner/releases/download/v1.9.0/osv-scanner_linux_amd64 -o /usr/local/bin/osv-scanner \
    && chmod +x /usr/local/bin/osv-scanner \
    && curl -fsSL https://github.com/github/codeql-cli-binaries/releases/latest/download/codeql-linux64.zip -o /tmp/codeql.zip \
    && unzip -q /tmp/codeql.zip -d /usr/local/ \
    && ln -s /usr/local/codeql/codeql /usr/local/bin/codeql \
    && rm -f /tmp/codeql.zip \
    && chown -R codespace:codespace /usr/local/codeql

# 10. Install WebAssembly Runtime (Wasmtime) & Rizin
RUN curl -fsSL https://github.com/bytecodealliance/wasmtime/releases/download/v26.0.0/wasmtime-v26.0.0-x86_64-linux.tar.xz | tar -xJ -C /tmp \
    && mv /tmp/wasmtime-*/wasmtime /usr/local/bin/wasmtime \
    && rm -rf /tmp/wasmtime-* \
    && chmod +x /usr/local/bin/wasmtime \
    && curl -fsSL https://github.com/rizinorg/rizin/releases/download/v0.7.2/rizin-v0.7.2-static-x86_64.tar.xz | tar -xJ -C /tmp \
    && mv /tmp/rizin-v0.7.2-static-x86_64/bin/* /usr/local/bin/ \
    && rm -rf /tmp/rizin-*

# 11. Configure Network Capture Permissions for Wireshark/tcpdump
RUN groupadd -g 150 wireshark || true \
    && usermod -a -G wireshark codespace \
    && chgrp wireshark /usr/bin/dumpcap 2>/dev/null || true \
    && chmod 750 /usr/bin/dumpcap 2>/dev/null || true \
    && setcap cap_net_raw,cap_net_admin=eip /usr/bin/dumpcap 2>/dev/null || true

# 12. Final User & Workdir Configuration
USER codespace
WORKDIR /workspaces

# Verify baseline installation
RUN java -version \
    && python3 --version \
    && node --version \
    && gcc --version \
    && clang --version \
    && cmake --version \
    && radare2 -v | head -n 1 \
    && yara -v \
    && trivy --version \
    && gitleaks version

CMD ["/bin/bash"]
