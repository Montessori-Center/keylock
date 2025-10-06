#!/usr/bin/env node
// /www/wwwroot/keylock.interschool.online/www/server.js

const { spawn } = require('child_process');
const path = require('path');

console.log('🚀 Starting Keylock application...');
console.log('Working directory:', __dirname);

// Функция для запуска процесса с логированием
function startProcess(name, command, cwd) {
    console.log(`Starting ${name}...`);
    const proc = spawn('bash', ['-c', command], {
        cwd: cwd,
        stdio: 'inherit',
        detached: false
    });
    
    proc.on('error', (err) => {
        console.error(`❌ ${name} error:`, err);
    });
    
    proc.on('exit', (code) => {
        console.log(`${name} exited with code ${code}`);
    });
    
    return proc;
}

// Запуск Backend (Flask)
const backendPath = path.join(__dirname, 'backend');
const backendCommand = `
    if [ -f venv/bin/activate ]; then
        source venv/bin/activate
    fi
    python3 app.py
`;
const backend = startProcess('Backend', backendCommand, backendPath);

// Небольшая задержка перед запуском frontend
setTimeout(() => {
    // Запуск Frontend (React)
    const frontendPath = path.join(__dirname, 'frontend');
    const frontendCommand = 'npm start';
    const frontend = startProcess('Frontend', frontendCommand, frontendPath);
    
    // Обработка завершения процессов
    process.on('SIGINT', () => {
        console.log('\n🛑 Received SIGINT, stopping processes...');
        backend.kill('SIGTERM');
        frontend.kill('SIGTERM');
        setTimeout(() => {
            process.exit(0);
        }, 1000);
    });
    
    process.on('SIGTERM', () => {
        console.log('\n🛑 Received SIGTERM, stopping processes...');
        backend.kill('SIGTERM');
        frontend.kill('SIGTERM');
        setTimeout(() => {
            process.exit(0);
        }, 1000);
    });
}, 3000);