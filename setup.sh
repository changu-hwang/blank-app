#!/bin/sh
# Install RTK AI - CLI proxy that reduces LLM token consumption by 60-90%
curl -fsSL https://raw.githubusercontent.com/rtk-ai/rtk/refs/heads/master/install.sh | sh

echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
export PATH="$HOME/.local/bin:$PATH"

rtk --version

# Install Google Workspace CLI (gws)
npm install -g @googleworkspace/cli
gws --version
