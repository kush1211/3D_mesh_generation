FROM python:3.12-slim-bookworm
COPY docker/requirements-exec.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt \
    && rm /tmp/requirements.txt
WORKDIR /work
# Non-root enforced at runtime via --user host_uid:host_gid
