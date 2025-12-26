#!/bin/bash
# =============================================================================
# CAD-to-3D Print Converter - Installation Script
# =============================================================================
# 
# This script installs all required dependencies for the conversion system.
# Supports: Ubuntu/Debian, Raspberry Pi OS, macOS
#
# Author: Tech Sierra Solutions
# License: MIT
# =============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
echo "╔════════════════════════════════════════════════════════════╗"
echo "║       CAD-to-3D Print Converter - Installation            ║"
echo "║                   Version 1.0.0                           ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Detect OS
detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if [ -f /etc/os-release ]; then
            . /etc/os-release
            OS=$NAME
            VER=$VERSION_ID
        fi
        if [[ "$OS" == *"Raspbian"* ]] || [[ "$OS" == *"Raspberry"* ]]; then
            PLATFORM="raspberry"
        else
            PLATFORM="linux"
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        PLATFORM="macos"
        OS="macOS"
    else
        PLATFORM="unknown"
    fi
    
    echo -e "${GREEN}Detected: $OS ($PLATFORM)${NC}"
}

# Install system dependencies
install_system_deps() {
    echo -e "\n${YELLOW}Installing system dependencies...${NC}"
    
    if [[ "$PLATFORM" == "linux" ]] || [[ "$PLATFORM" == "raspberry" ]]; then
        sudo apt-get update
        sudo apt-get install -y \
            python3 \
            python3-pip \
            python3-venv \
            git \
            wget \
            curl \
            build-essential \
            libffi-dev \
            libssl-dev \
            libjpeg-dev \
            zlib1g-dev \
            libfreetype6-dev \
            libgeos-dev \
            libproj-dev \
            cmake \
            ninja-build
        
    elif [[ "$PLATFORM" == "macos" ]]; then
        # Check for Homebrew
        if ! command -v brew &> /dev/null; then
            echo -e "${YELLOW}Installing Homebrew...${NC}"
            /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        fi
        
        brew install python3 git wget cmake ninja geos proj
    fi
}

# Install FreeCAD
install_freecad() {
    echo -e "\n${YELLOW}Installing FreeCAD...${NC}"
    
    if [[ "$PLATFORM" == "linux" ]]; then
        # Add FreeCAD PPA
        sudo add-apt-repository -y ppa:freecad-maintainers/freecad-stable
        sudo apt-get update
        sudo apt-get install -y freecad
        
    elif [[ "$PLATFORM" == "raspberry" ]]; then
        # Raspberry Pi - build from source or use AppImage
        echo -e "${YELLOW}FreeCAD installation on Raspberry Pi is limited.${NC}"
        echo "Consider using the companion server on a more powerful machine."
        
        # Install FreeCAD from apt (may be older version)
        sudo apt-get install -y freecad || true
        
    elif [[ "$PLATFORM" == "macos" ]]; then
        brew install --cask freecad
    fi
}

# Install ODA File Converter
install_oda() {
    echo -e "\n${YELLOW}Installing ODA File Converter...${NC}"
    
    ODA_URL=""
    
    if [[ "$PLATFORM" == "linux" ]]; then
        # Check architecture
        ARCH=$(uname -m)
        if [[ "$ARCH" == "x86_64" ]]; then
            ODA_URL="https://download.opendesign.com/guestfiles/Demo/ODAFileConverter_QT6_lnxX64_8.3dll_25.3.deb"
        elif [[ "$ARCH" == "aarch64" ]]; then
            echo -e "${YELLOW}ODA File Converter not available for ARM64.${NC}"
            echo "DWG/DGN conversion will require alternative tools."
            return
        fi
        
        if [ -n "$ODA_URL" ]; then
            wget -O /tmp/oda_converter.deb "$ODA_URL"
            sudo dpkg -i /tmp/oda_converter.deb || sudo apt-get install -f -y
            rm /tmp/oda_converter.deb
        fi
        
    elif [[ "$PLATFORM" == "macos" ]]; then
        echo -e "${YELLOW}Please download ODA File Converter manually from:${NC}"
        echo "https://www.opendesign.com/guestfiles/oda_file_converter"
    fi
}

# Install Inkscape
install_inkscape() {
    echo -e "\n${YELLOW}Installing Inkscape...${NC}"
    
    if [[ "$PLATFORM" == "linux" ]] || [[ "$PLATFORM" == "raspberry" ]]; then
        sudo apt-get install -y inkscape
        
    elif [[ "$PLATFORM" == "macos" ]]; then
        brew install --cask inkscape
    fi
}

# Install PrusaSlicer
install_prusaslicer() {
    echo -e "\n${YELLOW}Installing PrusaSlicer...${NC}"
    
    if [[ "$PLATFORM" == "linux" ]]; then
        # Download AppImage
        PRUSA_VERSION="2.7.1"
        PRUSA_URL="https://github.com/prusa3d/PrusaSlicer/releases/download/version_${PRUSA_VERSION}/PrusaSlicer-${PRUSA_VERSION}+linux-x64-GTK3-202311231454.AppImage"
        
        sudo wget -O /usr/local/bin/prusaslicer "$PRUSA_URL"
        sudo chmod +x /usr/local/bin/prusaslicer
        
    elif [[ "$PLATFORM" == "raspberry" ]]; then
        echo -e "${YELLOW}PrusaSlicer not available for Raspberry Pi ARM.${NC}"
        echo "Using built-in simple slicer or Cura."
        
        # Try to install Cura as alternative
        sudo apt-get install -y cura || true
        
    elif [[ "$PLATFORM" == "macos" ]]; then
        brew install --cask prusaslicer
    fi
}

# Install OpenSCAD
install_openscad() {
    echo -e "\n${YELLOW}Installing OpenSCAD...${NC}"
    
    if [[ "$PLATFORM" == "linux" ]] || [[ "$PLATFORM" == "raspberry" ]]; then
        sudo apt-get install -y openscad
        
    elif [[ "$PLATFORM" == "macos" ]]; then
        brew install --cask openscad
    fi
}

# Setup Python environment
setup_python() {
    echo -e "\n${YELLOW}Setting up Python environment...${NC}"
    
    # Create virtual environment
    python3 -m venv venv
    source venv/bin/activate
    
    # Upgrade pip
    pip install --upgrade pip wheel setuptools
    
    # Install requirements
    pip install -r software/requirements.txt
    
    echo -e "${GREEN}Python environment ready.${NC}"
}

# Install PlatformIO for ESP32 development
install_platformio() {
    echo -e "\n${YELLOW}Installing PlatformIO for ESP32 development...${NC}"
    
    source venv/bin/activate
    pip install platformio
    
    # Install ESP32 platform
    pio platform install espressif32
    
    echo -e "${GREEN}PlatformIO installed.${NC}"
}

# Create systemd service (Linux only)
create_service() {
    if [[ "$PLATFORM" != "linux" ]] && [[ "$PLATFORM" != "raspberry" ]]; then
        return
    fi
    
    echo -e "\n${YELLOW}Creating systemd service...${NC}"
    
    INSTALL_DIR=$(pwd)
    
    sudo tee /etc/systemd/system/3d-converter.service > /dev/null << EOF
[Unit]
Description=CAD-to-3D Print Converter Server
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$INSTALL_DIR
ExecStart=$INSTALL_DIR/venv/bin/python -m uvicorn software.server:app --host 0.0.0.0 --port 8000
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
    
    sudo systemctl daemon-reload
    sudo systemctl enable 3d-converter.service
    
    echo -e "${GREEN}Service created. Start with: sudo systemctl start 3d-converter${NC}"
}

# Build ESP32 firmware
build_firmware() {
    echo -e "\n${YELLOW}Building ESP32 firmware...${NC}"
    
    source venv/bin/activate
    cd firmware
    
    pio run
    
    echo -e "${GREEN}Firmware built. Flash with: pio run -t upload${NC}"
    cd ..
}

# Print summary
print_summary() {
    echo -e "\n${BLUE}"
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║                 Installation Complete!                     ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    
    echo -e "${GREEN}Installed components:${NC}"
    
    command -v freecad &> /dev/null && echo "  ✓ FreeCAD" || echo "  ✗ FreeCAD"
    command -v ODAFileConverter &> /dev/null && echo "  ✓ ODA File Converter" || echo "  ✗ ODA File Converter"
    command -v inkscape &> /dev/null && echo "  ✓ Inkscape" || echo "  ✗ Inkscape"
    command -v openscad &> /dev/null && echo "  ✓ OpenSCAD" || echo "  ✗ OpenSCAD"
    (command -v prusaslicer || command -v prusa-slicer) &> /dev/null && echo "  ✓ PrusaSlicer" || echo "  ✗ PrusaSlicer"
    
    echo ""
    echo -e "${YELLOW}Quick Start:${NC}"
    echo "  1. Activate virtual environment:"
    echo "     source venv/bin/activate"
    echo ""
    echo "  2. Start the conversion server:"
    echo "     python software/server.py"
    echo ""
    echo "  3. Access web interface:"
    echo "     http://localhost:8000"
    echo ""
    echo "  4. Flash ESP32 firmware:"
    echo "     cd firmware && pio run -t upload"
    echo ""
    echo -e "${BLUE}Documentation: docs/ARCHITECTURE.md${NC}"
}

# Main installation flow
main() {
    detect_os
    
    echo ""
    echo "This will install the following components:"
    echo "  - Python 3 and dependencies"
    echo "  - FreeCAD (CAD processing)"
    echo "  - ODA File Converter (DWG/DGN support)"
    echo "  - Inkscape (PDF/SVG conversion)"
    echo "  - OpenSCAD (parametric modeling)"
    echo "  - PrusaSlicer (G-code generation)"
    echo "  - PlatformIO (ESP32 development)"
    echo ""
    
    read -p "Continue with installation? (y/n) " -n 1 -r
    echo
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Installation cancelled."
        exit 1
    fi
    
    install_system_deps
    install_freecad
    install_oda
    install_inkscape
    install_openscad
    install_prusaslicer
    setup_python
    install_platformio
    
    if [[ "$PLATFORM" == "linux" ]] || [[ "$PLATFORM" == "raspberry" ]]; then
        read -p "Create systemd service for auto-start? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            create_service
        fi
    fi
    
    read -p "Build ESP32 firmware now? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        build_firmware
    fi
    
    print_summary
}

# Run main
main "$@"
