FROM python:3.12-slim AS nsjail-build

# Runtime + build deps
RUN apt-get update && apt-get install -y \
    git make g++ clang pkg-config flex bison \
    libprotobuf-dev protobuf-compiler \
    libnl-3-dev libnl-route-3-dev \
    util-linux ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Build nsjail inside container
RUN git clone https://github.com/google/nsjail.git /tmp/nsjail \
    && cd /tmp/nsjail \
    && make USE_STATIC_LIBS=1 \
    && cp nsjail /nsjail \
    && rm -rf /tmp/nsjail

FROM python:3.12-slim
COPY --from=nsjail-build /nsjail /usr/local/bin/nsjail
RUN chmod +x /usr/local/bin/nsjail

# Copy required libraries
COPY --from=nsjail-build /usr/lib/x86_64-linux-gnu/libprotobuf.so.32 /usr/lib/x86_64-linux-gnu/
COPY --from=nsjail-build /usr/lib/x86_64-linux-gnu/libnl-3.so.200 /usr/lib/x86_64-linux-gnu/
COPY --from=nsjail-build /usr/lib/x86_64-linux-gnu/libnl-route-3.so.200 /usr/lib/x86_64-linux-gnu/
COPY --from=nsjail-build /usr/lib/x86_64-linux-gnu/libstdc++.so.6 /usr/lib/x86_64-linux-gnu/

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

RUN useradd -m game
USER game

CMD ["python", "game.py"]
