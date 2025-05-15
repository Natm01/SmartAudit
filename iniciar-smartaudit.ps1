# Configurar el entorno Node.js
Write-Host "1. Configurando entorno Node.js..." -ForegroundColor Green
$env:PATH += ";C:\Users\mngonzalez\node-v17.9.1-win-x64"
$env:NODE_PATH = "C:\Users\mngonzalez\node-v17.9.1-win-x64\node_modules"

# Ir a la carpeta correcta
Write-Host "2. Accediendo al proyecto..." -ForegroundColor Green
Set-Location -Path "C:\Users\mngonzalez\Downloads\smartaudit"

# Ir al frontend
Write-Host "3. Accediendo al frontend..." -ForegroundColor Green
Set-Location -Path ".\frontend"

# Mostrar información de Node.js
Write-Host "Versión de Node.js: $(node --version)" -ForegroundColor Cyan
Write-Host "Versión de npm: $(npm --version)" -ForegroundColor Cyan

# Instalar dependencias primero
Write-Host "4. Instalando dependencias (esto puede tomar unos minutos)..." -ForegroundColor Yellow
npm install

npm install tailwindcss postcss autoprefixer

npx tailwindcss init -p


# Iniciar la aplicación
Write-Host "5. Iniciando la aplicación..." -ForegroundColor Green
npm start