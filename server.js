// /www/wwwroot/keylock.interschool.online/www/server.js
const { spawn } = require('child_process');
const path = require('path');

console.log('🚀 Starting Keylock application...');

// Запуск backend (Flask) с активацией venv
const backendPath = path.join(__dirname, 'backend');
const venvPath = path.join(backendPath, 'venv', 'bin', 'activate');

// Команда для запуска Flask с venv
const backendCommand = `source ${venvPath} && python3 app.py`;

const backend = spawn('bash', ['-c', backendCommand], {
  cwd: backendPath,
  stdio: 'inherit'
});

// Запуск frontend (React)
const frontend = spawn('npm', ['start'], {
  cwd: path.join(__dirname, 'frontend'),
  stdio: 'inherit'
});

backend.on('error', (err) => {
  console.error('❌ Backend error:', err);
});

frontend.on('error', (err) => {
  console.error('❌ Frontend error:', err);
});

// Graceful shutdown
process.on('SIGINT', () => {
  console.log('🛑 Stopping processes...');
  backend.kill();
  frontend.kill();
  process.exit(0);
});

process.on('SIGTERM', () => {
  console.log('🛑 Stopping processes...');
  backend.kill();
  frontend.kill();
  process.exit(0);
});