#!/usr/bin/env bash
# packaging/install.sh — Canonical installer for my-lisp and all execution islands
# Автоматично визначає пакетний менеджер і встановлює всі залежності островів.
set -euo pipefail

echo "==> my-lisp: встановлення інтерпретатора та всіх островів виконання..."

OS="$(uname -s)"
ARCH="$(uname -m)"

if [ "$OS" != "Linux" ] && [ "$OS" != "Darwin" ]; then
    echo "Помилка: цей скрипт призначено для Linux та macOS. Для Windows завантажте MSI-інсталятор із GitHub Releases." >&2
    exit 1
fi

# Перевіряємо платформу до створення каталогів або встановлення пакетів.
if [ "$OS" = "Linux" ] && [ "$ARCH" = "x86_64" ]; then
    ASSET_NAME="my-lisp-cli_0.40.2_linux_amd64"
elif [ "$OS" = "Darwin" ] && [ "$ARCH" = "arm64" ]; then
    ASSET_NAME="my-lisp-cli_0.40.2_macos_arm64"
elif [ "$OS" = "Darwin" ] && [ "$ARCH" = "x86_64" ]; then
    ASSET_NAME="my-lisp-cli_0.40.2_macos_x64"
else
    echo "Помилка: непідтримувана платформа: $OS $ARCH" >&2
    exit 1
fi

INSTALL_DIR="${HOME}/.local/bin"
LOCAL_LIB="${HOME}/.local/lib"
mkdir -p "$INSTALL_DIR" "$LOCAL_LIB"

# ──────────────────────────────────────────────────────────────────────────────
# Допоміжні функції
# ──────────────────────────────────────────────────────────────────────────────

has() { command -v "$1" >/dev/null 2>&1; }

running_as_root() { [ "$(id -u)" = "0" ]; }

maybe_sudo() {
    if running_as_root; then
        "$@"
    else
        sudo "$@"
    fi
}

# ──────────────────────────────────────────────────────────────────────────────
# Встановлення системних залежностей: SBCL, SWI-Prolog, gcc, make, curl
# ──────────────────────────────────────────────────────────────────────────────

install_linux_deps() {
    local pkgs="sbcl swi-prolog gcc make curl"

    # ---- Guix (не потребує sudo, не потребує apt) --------------------------------
    if has guix; then
        echo "==> Guix виявлено — встановлюємо sbcl та swi-prolog через guix..."
        guix install sbcl swi-prolog
        # gcc/make/curl зазвичай є в guix-системі; якщо ні — встановимо
        has gcc   || guix install gcc-toolchain
        has curl  || guix install curl
        return 0
    fi

    # ---- apt-get (Debian, Ubuntu, Raspberry Pi OS) --------------------------------
    if has apt-get; then
        echo "==> apt-get виявлено — встановлюємо залежності..."
        maybe_sudo env DEBIAN_FRONTEND=noninteractive apt-get update -qq
        # swi-prolog в Ubuntu 22.04+ є; libclips-dev може бути застарілим — CLIPS
        # будуємо з source окремо нижче, тому тут не включаємо
        maybe_sudo env DEBIAN_FRONTEND=noninteractive apt-get install -y \
            sbcl swi-prolog gcc make curl
        return 0
    fi

    # ---- dnf / dnf5 (Fedora, RHEL, Rocky, Alma) ----------------------------------
    if has dnf5; then
        echo "==> dnf5 виявлено — встановлюємо залежності..."
        maybe_sudo dnf5 install -y sbcl swi-prolog gcc make curl
        return 0
    fi
    if has dnf; then
        echo "==> dnf виявлено — встановлюємо залежності..."
        maybe_sudo dnf install -y sbcl swi-prolog gcc make curl
        return 0
    fi

    # ---- pacman (Arch Linux, Manjaro) --------------------------------------------
    if has pacman; then
        echo "==> pacman виявлено — встановлюємо залежності..."
        maybe_sudo pacman -S --noconfirm sbcl swi-prolog gcc make curl
        return 0
    fi

    # ---- zypper (openSUSE) -------------------------------------------------------
    if has zypper; then
        echo "==> zypper виявлено — встановлюємо залежності..."
        maybe_sudo zypper install -y sbcl swi-prolog gcc make curl
        return 0
    fi

    echo "⚠️  Не вдалося визначити пакетний менеджер. Будь ласка, встановіть вручну:" >&2
    echo "    sbcl swi-prolog gcc make curl" >&2
}

install_macos_deps() {
    if ! has brew; then
        echo "==> Homebrew не знайдено. Встановлюємо Homebrew..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        # Додаємо brew до PATH для поточного сеансу
        if [ -f /opt/homebrew/bin/brew ]; then
            eval "$(/opt/homebrew/bin/brew shellenv)"
        elif [ -f /usr/local/bin/brew ]; then
            eval "$(/usr/local/bin/brew shellenv)"
        fi
    fi

    echo "==> brew виявлено — встановлюємо sbcl та swi-prolog..."
    brew install sbcl swi-prolog
}

# ──────────────────────────────────────────────────────────────────────────────
# CLIPS 6.4.2: перевірка наявності; якщо немає — збираємо з source
# CLIPS не постачається з правильним 6.4.2 C-ABI через більшість дистрибутивів,
# тому завжди будуємо з офіційного source tarball (~5 секунд)
# ──────────────────────────────────────────────────────────────────────────────

CLIPS_LIB=""
if [ "$OS" = "Darwin" ]; then
    CLIPS_LIB="${LOCAL_LIB}/libclips.dylib"
else
    CLIPS_LIB="${LOCAL_LIB}/libclips.so"
fi
CLIPS_BIN="${INSTALL_DIR}/clips"

ensure_clips() {
    if [ -f "$CLIPS_LIB" ] && [ -f "$CLIPS_BIN" ]; then
        echo "==> CLIPS 6.4.2 вже збудовано: ${CLIPS_LIB}"
        return 0
    fi

    echo "==> Завантаження та збирання CLIPS 6.4.2 з source..."
    local CLIPS_URL="https://sourceforge.net/projects/clipsrules/files/CLIPS/6.4.2/clips_core_source_642.tar.gz/download"
    local BUILD_TMP
    BUILD_TMP="$(mktemp -d)"
    local TARBALL="${BUILD_TMP}/clips_core_source_642.tar.gz"

    curl -fL --silent --max-time 120 "$CLIPS_URL" -o "$TARBALL" \
        || { echo "Помилка: не вдалося завантажити CLIPS source" >&2; rm -rf "$BUILD_TMP"; return 1; }

    tar -xzf "$TARBALL" -C "$BUILD_TMP"

    local SRC_DIR
    SRC_DIR="$(find "$BUILD_TMP" -maxdepth 2 -name '*.c' -exec dirname {} \; | sort -u | head -1)"
    if [ -z "$SRC_DIR" ]; then
        echo "Помилка: не вдалося знайти .c файли в архіві CLIPS" >&2
        rm -rf "$BUILD_TMP"
        return 1
    fi

    local CC="gcc"
    local SO_FLAG="-shared"
    local LIB_EXT="so"
    if [ "$OS" = "Darwin" ]; then
        CC="clang"
        SO_FLAG="-dynamiclib"
        LIB_EXT="dylib"
    fi
    local CFLAGS="-std=c99 -O3 -fPIC -fno-strict-aliasing"

    echo "==> Компіляція libclips.${LIB_EXT}..."
    (cd "$SRC_DIR" && $CC $SO_FLAG -o "$CLIPS_LIB" $CFLAGS ./*.c -lm)
    echo "==> Компіляція clips CLI..."
    (cd "$SRC_DIR" && $CC -o "$CLIPS_BIN" $CFLAGS ./*.c -lm)
    chmod +x "$CLIPS_BIN"

    rm -rf "$BUILD_TMP"
    echo "==> CLIPS 6.4.2 збудовано: ${CLIPS_LIB} та ${CLIPS_BIN}"
}

# ──────────────────────────────────────────────────────────────────────────────
# Встановлення залежностей
# ──────────────────────────────────────────────────────────────────────────────

echo "==> Встановлення системних залежностей островів..."
if [ "$OS" = "Linux" ]; then
    install_linux_deps
elif [ "$OS" = "Darwin" ]; then
    install_macos_deps
fi

echo "==> Перевірка/збірка CLIPS 6.4.2..."
ensure_clips

# ──────────────────────────────────────────────────────────────────────────────
# Завантаження my-lisp
# ──────────────────────────────────────────────────────────────────────────────

MY_LISP_TARGET="${INSTALL_DIR}/my-lisp"

# Оновлюємо саме користувацьку копію, незалежно від старих CLI у PATH.
# Тимчасовий файл поруч із ціллю дозволяє замінити її одним rename.
echo "==> Завантаження my-lisp (${ASSET_NAME})..."
DOWNLOAD_URL="https://github.com/juv4uk/my-lisp/releases/download/l0.40.2/${ASSET_NAME}"
CLI_TEMP="$(mktemp "${INSTALL_DIR}/.my-lisp.XXXXXX")"
trap 'rm -f "$CLI_TEMP"' EXIT
curl -fL --silent --show-error --connect-timeout 15 --max-time 120 \
    "$DOWNLOAD_URL" -o "$CLI_TEMP"
test -s "$CLI_TEMP"
chmod 755 "$CLI_TEMP"
# Не замінюємо попередній файл, якщо новий CLI навіть не запускається.
CLI_VERSION="$("$CLI_TEMP" --version)"
mv -f "$CLI_TEMP" "$MY_LISP_TARGET"
trap - EXIT
export PATH="${INSTALL_DIR}:${PATH}"

EXE="$MY_LISP_TARGET"
echo "==> my-lisp готовий до роботи: ${CLI_VERSION}"

# ──────────────────────────────────────────────────────────────────────────────
# Встановлення решти островів через my-lisp install
# (Datalog — embedded; SBCL та SWI-Prolog вже встановлені вище)
# ──────────────────────────────────────────────────────────────────────────────

echo "==> Реєстрація всіх 4 островів виконання (four-kernel profile)..."
"$EXE" install --profile four-kernel

echo "==> Перевірка доступності ядер:"
"$EXE" islands status

echo ""
echo "==> Готово! my-lisp та всі 4 острови виконання успішно встановлено:"
echo "    • Common Lisp (SBCL)"
echo "    • Prolog (SWI-Prolog)"
echo "    • CLIPS 6.4.2"
echo "    • Datalog (вбудований)"
echo ""
echo "    Переконайтесь що ${INSTALL_DIR} є у вашому PATH:"
echo "    export PATH=\"\${HOME}/.local/bin:\${PATH}\""
