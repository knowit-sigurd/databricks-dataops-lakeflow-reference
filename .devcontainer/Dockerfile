# This is based on https://www.linkedin.com/pulse/building-custom-devcontainer-pyspark-aws-development-chris-mamon/
FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive

# Unminimize and install packages
RUN apt-get update && yes | unminimize
RUN apt-get update \
    && apt-get install -y \
        git \
        wget \
        curl \
        build-essential \
        libssl-dev \
        zlib1g-dev \
        libbz2-dev \
        libreadline-dev \
        libsqlite3-dev \
        llvm \
        libncurses5-dev \
        libncursesw5-dev \
        default-jdk \
        default-jre \
        scala \
        man-db \
        shellcheck \
        unzip \
        xz-utils \
        tk-dev \
        libffi-dev \
        liblzma-dev \
        libsasl2-dev \
        sudo \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create a non-root user that matches GitHub Actions workspace UID/GID
ARG USERNAME=app
ARG UID=1001
ARG GID=1001
RUN groupadd --gid "$GID" "$USERNAME" \
    && useradd --uid "$UID" --gid "$GID" -m -s /bin/bash "$USERNAME"

ENV UV_INSTALL_DIR=/usr/local/bin
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

RUN curl -fsSL https://raw.githubusercontent.com/databricks/setup-cli/main/install.sh | sh

ARG SPARK_VERSION=4.1.1
ARG HADOOP_FLAVOR=hadoop3
RUN wget -q https://downloads.apache.org/spark/spark-${SPARK_VERSION}/spark-${SPARK_VERSION}-bin-${HADOOP_FLAVOR}.tgz \
    && tar -xzf spark-${SPARK_VERSION}-bin-${HADOOP_FLAVOR}.tgz \
    && mv spark-${SPARK_VERSION}-bin-${HADOOP_FLAVOR} /opt/spark \
    && rm spark-${SPARK_VERSION}-bin-${HADOOP_FLAVOR}.tgz \
    && chown -R "$UID:$GID" /opt/spark

ENV SPARK_HOME=/opt/spark
ENV PATH="$PATH:$SPARK_HOME/bin"

# Switch to non-root, set HOME and prepare cache dirs
USER $USERNAME
ENV HOME=/home/$USERNAME
RUN mkdir -p "$HOME/.cache/uv" "$HOME/workspace"

# Warm Spark/Delta deps as the non-root user so caches land in $HOME/.ivy2
WORKDIR /home/$USERNAME
# Register extra packages for hadoop (catalog support), and delta table support
RUN echo "import sys" > dummy.py \
    && ${SPARK_HOME}/bin/spark-submit \
         --packages org.apache.hadoop:hadoop-azure:3.4.2,io.delta:delta-core_2.12:2.4.0 \
         dummy.py \
    && rm dummy.py

# Default workdir (GitHub Actions will still run steps in $GITHUB_WORKSPACE)
WORKDIR /home/$USERNAME/workspace
