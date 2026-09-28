#!/bin/bash
set -e

SERVER="root@100.113.68.50"
# Build locally
echo "Building release binary locally via Guix..."
guix shell -m manifest.scm -- cargo build --release -p sens-cli

# The semantic Oracle is a release-only service.  Fail closed if the build
# produced no release artifact; never fall back to target/debug/my-lisp.
ORACLE_BINARY="${ORACLE_BINARY:-/home/my-lisp/.cache/my-lisp-target/release/my-lisp}"
if [ ! -x "$ORACLE_BINARY" ]; then
  echo "ERROR: release Oracle binary missing or not executable: $ORACLE_BINARY" >&2
  exit 1
fi
echo "Using release Oracle: $ORACLE_BINARY"

echo "Uploading binary to server..."
scp -o StrictHostKeyChecking=no "$ORACLE_BINARY" $SERVER:/root/my-lisp-new

echo "Executing deployment on server..."
ssh -o StrictHostKeyChecking=no $SERVER 'bash -s' << 'EOF'
  set -e
  # Identify which one is currently running
  if systemctl is-active --quiet my-lisp-blue.service; then
      ACTIVE="blue"
      INACTIVE="green"
      echo "Currently active: BLUE. Deploying to GREEN..."
  else
      ACTIVE="green"
      INACTIVE="blue"
      echo "Currently active: GREEN (or none). Deploying to BLUE..."
  fi

  echo "Copying binary to /opt/my-lisp/$INACTIVE/ ..."
  mv /root/my-lisp-new /opt/my-lisp/$INACTIVE/my-lisp
  chmod +x /opt/my-lisp/$INACTIVE/my-lisp
  patchelf --set-interpreter /lib64/ld-linux-x86-64.so.2 /opt/my-lisp/$INACTIVE/my-lisp

  echo "Starting my-lisp-$INACTIVE.service..."
  systemctl start my-lisp-$INACTIVE.service
  systemctl enable my-lisp-$INACTIVE.service

  echo "Waiting for service to bind and HAProxy to recognize..."
  sleep 3

  if systemctl is-active --quiet my-lisp-$ACTIVE.service; then
      echo "Stopping old active service (my-lisp-$ACTIVE.service) to force client reconnect..."
      systemctl stop my-lisp-$ACTIVE.service
      systemctl disable my-lisp-$ACTIVE.service
  fi

  echo "Deployment complete! Active instance is now $INACTIVE."
  systemctl status my-lisp-$INACTIVE.service --no-pager
EOF
