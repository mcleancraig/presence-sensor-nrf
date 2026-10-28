#!/usr/bin/env zsh
# Environment configuration for Zephyr / nRF Connect SDK development

# Activate the dedicated Python 3.12 virtual environment
source ~/.ncs-venv/bin/activate

# Set Zephyr Base and SDK Toolchain variables
export ZEPHYR_BASE="${HOME}/ncs/zephyr"
export ZEPHYR_TOOLCHAIN_VARIANT="zephyr"
export ZEPHYR_SDK_INSTALL_DIR="${HOME}/zephyr-sdk-0.16.8"

echo "nRF Connect SDK & Zephyr environment loaded:"
echo "  ZEPHYR_BASE:            $ZEPHYR_BASE"
echo "  ZEPHYR_SDK_INSTALL_DIR: $ZEPHYR_SDK_INSTALL_DIR"
echo "  Python venv:            $(which python)"
echo "  Compiler:               $(arm-zephyr-eabi-gcc --version 2>/dev/null | head -n 1)"
