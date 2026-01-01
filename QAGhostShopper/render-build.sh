#!/bin/bash
set -e

echo "=========================================="
echo "Instalando Google Chrome en Render..."
echo "=========================================="

# Actualizar repositorios
apt-get update

# Instalar dependencias de Chrome
apt-get install -y \
    wget \
    gnupg2 \
    apt-transport-https \
    ca-certificates

# Agregar repositorio de Google Chrome
wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - 
echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google.list

# Actualizar nuevamente
apt-get update

# Instalar Google Chrome Stable
apt-get install -y google-chrome-stable

# Verificar que Chrome se instaló correctamente
echo "=========================================="
echo "Chrome instalado correctamente:"
google-chrome --version
echo "=========================================="

# Instalar Python dependencies
pip install --upgrade pip
pip install -r requirements.txt

echo "=========================================="
echo "✓ Instalación completada exitosamente"
echo "=========================================="
