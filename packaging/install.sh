#!/usr/bin/env bash
# packaging/install.sh — Canonical installer for my-lisp and all execution islands
set -euo pipefail

echo "==> my-lisp: встановлення інтерпретатора та всіх островів виконання..."

OS="$(uname -s)"
ARCH="$(uname -m)"

if [ "$OS" != "Linux" ] && [ "$OS" != "Darwin" ]; then
    echo "Помилка: цей скрипт призначено для Linux та macOS. Для Windows завантажте MSI-інсталятор із GitHub Releases." >&2
    exit 1
fi

INSTALL_DIR="${HOME}/.local/bin"
mkdir -p "$INSTALL_DIR"

if [ "$OS" = "Linux" ] && [ "$ARCH" = "x86_64" ]; then
    ASSET_NAME="my-lisp-cli_0.40.0_linux_amd64"
elif [ "$OS" = "Darwin" ] && [ "$ARCH" = "arm64" ]; then
    ASSET_NAME="my-lisp-cli_0.40.0_macos_arm64"
elif [ "$OS" = "Darwin" ]; then
    ASSET_NAME="my-lisp-cli_0.40.0_macos_x64"
else
    echo "Помилка: непідтримувана платформа: $OS $ARCH" >&2
    exit 1
fi

MY_LISP_TARGET="${INSTALL_DIR}/my-lisp"

# Завантажуємо свіжий бінарник my-lisp, якщо він ще не встановлений у системі
if ! command -v my-lisp >/dev/null 2>&1; then
    echo "==> Завантаження my-lisp (${ASSET_NAME})..."
    DOWNLOAD_URL="https://github.com/juv4uk/my-lisp/releases/latest/download/${ASSET_NAME}"
    if ! curl -fL "$DOWNLOAD_URL" -o "$MY_LISP_TARGET" 2>/dev/null; then
        # Fallback до релізу l0.40.0
        curl -fL "https://github.com/juv4uk/my-lisp/releases/download/l0.40.0/${ASSET_NAME}" -o "$MY_LISP_TARGET"
    fi
    chmod +x "$MY_LISP_TARGET"
    export PATH="${INSTALL_DIR}:${PATH}"
fi

EXE="$(command -v my-lisp || echo "$MY_LISP_TARGET")"
echo "==> my-lisp готовий до роботи: $("$EXE" --version)"

# Встановлюємо всі 4 острови виконання автоматично
echo "==> Встановлення всіх островів виконання (four-kernel profile)..."
"$EXE" install --profile four-kernel

echo "==> Перевірка доступності ядер:"
"$EXE" islands status

echo ""
echo "==> Готово! my-lisp та всі 4 острови виконання (Common Lisp, Prolog, CLIPS, Datalog) успішно встановлено."
