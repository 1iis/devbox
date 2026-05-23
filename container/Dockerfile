FROM ubuntu:24.04

ARG UID=1111
ARG GID=1111
ENV DEBIAN_FRONTEND=noninteractive

# Base packages
RUN apt-get update && apt-get install -y \
    build-essential git curl zsh nano python-is-python3 kitty-terminfo \
    btop htop jq yq fzf ripgrep fd-find tree bat tldr \
    rclone strace netcat-openbsd tcpdump acl \
    docker.io sudo ca-certificates unzip \
    bubblewrap \
    && rm -rf /var/lib/apt/lists/*

# Create user/group with explicit UID/GID (same as host dev user)
RUN groupadd --gid ${GID} dev && \
    useradd --uid ${UID} --gid ${GID} --create-home --shell /usr/bin/zsh --groups sudo --no-log-init dev && \
    mkdir -p /etc/sudoers.d && \
    echo "dev ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/dev && \
    chmod 0440 /etc/sudoers.d/dev

# uv
RUN curl -LsSf https://astral.sh/uv/install.sh | env UV_INSTALL_DIR=/usr/local/bin sh

# GitHub CLI
RUN mkdir -p /etc/apt/keyrings && \
    curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg -o /etc/apt/keyrings/githubcli-archive-keyring.gpg && \
    chmod go+r /etc/apt/keyrings/githubcli-archive-keyring.gpg && \
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" \
      > /etc/apt/sources.list.d/github-cli.list && \
    apt-get update && apt-get install -y gh && \
    rm -rf /var/lib/apt/lists/*

# Node.js LTS (prebuilt binary)
RUN curl -fsSL https://nodejs.org/dist/v24.15.0/node-v24.15.0-linux-x64.tar.xz \
    | tar -xJf - -C /opt --transform='s/^node-v24.15.0-linux-x64/node/' \
    && mkdir -p /home/dev/.npm/global \
    && chown -R dev:dev /home/dev/.npm

# Oh My Zsh
RUN su -l dev -c 'RUNZSH=no CHSH=no sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"'

# p10k
RUN su -l dev -c 'git clone --depth=1 https://github.com/romkatv/powerlevel10k.git ${ZSH_CUSTOM:-$HOME/.oh-my-zsh/custom}/themes/powerlevel10k'

# Plugins
RUN su -l dev -c 'git clone --depth=1 https://github.com/zsh-users/zsh-autosuggestions ${ZSH_CUSTOM:-$HOME/.oh-my-zsh/custom}/plugins/zsh-autosuggestions'
RUN su -l dev -c 'git clone --depth=1 https://github.com/zsh-users/zsh-syntax-highlighting.git ${ZSH_CUSTOM:-$HOME/.oh-my-zsh/custom}/plugins/zsh-syntax-highlighting'

# User-specific
USER dev
WORKDIR /home/dev

# Pre-create directories that volume mounts would otherwise auto-create as root
RUN mkdir -p ~/.config/gh ~/.ssh ~/.codex

# npm global prefix + Codex CLI
RUN PATH="/opt/node/bin:$PATH" /opt/node/bin/npm config set prefix /home/dev/.npm/global
RUN PATH="/opt/node/bin:$PATH" /opt/node/bin/npm install -g @openai/codex

# Keep container alive; enter with: docker compose exec dev zsh
CMD ["sleep", "infinity"]
