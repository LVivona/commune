
# syntax=docker/dockerfile:1
FROM nvidia/cuda:12.0.0-runtime-ubuntu22.04

RUN rm -f /etc/apt/sources.list.d/*.list
WORKDIR /app

ARG DEBIAN_FRONTEND=noninteractive

RUN apt update && apt upgrade -y
RUN apt install -y curl sudo nano git htop netcat wget unzip python3-dev python3-pip tmux apt-utils cmake build-essential

## Upgrade pip
RUN pip3 install --upgrade pip
RUN apt install -y protobuf-compiler

# NPM LAND

ENV NODE_VERSION=16.17.1
RUN apt install -y curl
RUN curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
ENV NVM_DIR=/root/.nvm
RUN . "$NVM_DIR/nvm.sh" && nvm install ${NODE_VERSION}
RUN . "$NVM_DIR/nvm.sh" && nvm use v${NODE_VERSION}
RUN . "$NVM_DIR/nvm.sh" && nvm alias default v${NODE_VERSION}
ENV PATH="/root/.nvm/versions/node/v${NODE_VERSION}/bin/:${PATH}"
RUN node --version
RUN npm --version

RUN npm i -g pm2

# we add sprinkle of npm for hardhat smart contract tings
ENV NODE_VERSION=16.17.1
RUN apt install -y curl
RUN curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
ENV NVM_DIR=/root/.nvm
RUN . "$NVM_DIR/nvm.sh" && nvm install ${NODE_VERSION}
RUN . "$NVM_DIR/nvm.sh" && nvm use v${NODE_VERSION}
RUN . "$NVM_DIR/nvm.sh" && nvm alias default v${NODE_VERSION}
ENV PATH="/root/.nvm/versions/node/v${NODE_VERSION}/bin/:${PATH}"
RUN node --version
RUN npm --version
RUN npm install --save-dev hardhat
RUN npm install --save-dev @nomicfoundation/hardhat-toolbox
COPY hardhat.config.js .
RUN npx hardhat
RUN npm install @openzeppelin/contracts
RUN npm install @uniswap/v3-periphery
RUN npm install @uniswap/v2-periphery
# RUN npm install --global @ceramicnetwork/cli @glazed/cli

# RUST LAND


# Install cargo and Rust
RUN curl https://sh.rustup.rs -sSf | sh -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"

RUN apt-get update \
 && DEBIAN_FRONTEND=noninteractive \
    apt-get install --no-install-recommends --assume-yes \
      protobuf-compiler

RUN rustup update nightly
RUN rustup target add wasm32-unknown-unknown --toolchain nightly
RUN apt-get install make
RUN apt-get install -y pkg-config

# INK CONTRACTS STUFF
RUN apt install binaryen
RUN apt-get install libssl-dev
RUN cargo install cargo-dylint dylint-link
RUN cargo install cargo-contract --force

RUN rustup component add rust-src --toolchain nightly-x86_64-unknown-linux-gnu


# COPY SRC AND INSTALL AS A PACKAGE

# INSTALL PACKAGES BEFORE COMMUNE
RUN pip install bittensor

RUN pip install jupyterlab

# INSTALL COMMUNE
COPY ./commune /app/commune
COPY ./scripts /app/scripts
COPY ./requirements.txt /app/requirements.txt
COPY ./setup.py /app/setup.py
COPY ./README.md /app/README.md
RUN pip install -e .
RUN pip install openai
RUN pip install google-search-results
RUN pip install wikipedia
RUN pip install pytest
# BITTENSOR HAS AN OLD VERSION OF SUBSTRATE THIS UP TOO
RUN pip install --upgrade substrate-interface
RUN pip install accelerate


