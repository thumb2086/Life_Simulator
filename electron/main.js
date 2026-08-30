/**
 * Life Simulator — Electron Main Process
 * Starts FastAPI backend, opens a frameless BrowserWindow pointing at it.
 */

const { app, BrowserWindow, dialog } = require('electron');
const { spawn } = require('child_process');
const path = require('path');
const http = require('http');

// ── Config ──────────────────────────────────────────────────────────
const PORT = 18732;  // Random high port to avoid conflicts
const SERVER_URL = `http://127.0.0.1:${PORT}`;
const STARTUP_TIMEOUT = 15000; // 15s to wait for server

// ── Globals ─────────────────────────────────────────────────────────
let mainWindow = null;
let serverProcess = null;

// ── Find Python ─────────────────────────────────────────────────────
function findPython() {
  // Prefer the same Python that's running this project
  const candidates = [
    process.env.PYTHON_PATH,
    'python',
    'python3',
    'py',
  ].filter(Boolean);

  return candidates[0]; // Use first available
}

// ── Start FastAPI server ────────────────────────────────────────────
function startServer() {
  return new Promise((resolve, reject) => {
    const python = findPython();
    const scriptPath = path.join(__dirname, '..', 'api_server.py');

    console.log(`Starting server: ${python} ${scriptPath} on port ${PORT}`);

    serverProcess = spawn(python, ['-m', 'uvicorn', 'api_server:app',
      '--host', '127.0.0.1', '--port', String(PORT)],
      {
        cwd: path.join(__dirname, '..'),
        stdio: ['pipe', 'pipe', 'pipe'],
        env: { ...process.env, PYTHONUNBUFFERED: '1' },
      }
    );

    serverProcess.stdout.on('data', (data) => {
      const msg = data.toString();
      console.log('[server]', msg.trim());
      if (msg.includes('Application startup complete')) {
        resolve();
      }
    });

    serverProcess.stderr.on('data', (data) => {
      console.error('[server err]', data.toString().trim());
    });

    serverProcess.on('error', (err) => {
      console.error('Failed to start server:', err);
      reject(err);
    });

    serverProcess.on('exit', (code) => {
      console.log(`Server exited with code ${code}`);
      if (code !== null && code !== 0) {
        reject(new Error(`Server exited with code ${code}`));
      }
    });

    // Timeout fallback — poll the server
    const startTime = Date.now();
    const poll = setInterval(() => {
      if (Date.now() - startTime > STARTUP_TIMEOUT) {
        clearInterval(poll);
        reject(new Error('Server startup timeout'));
        return;
      }
      http.get(SERVER_URL + '/api/status', (res) => {
        if (res.statusCode === 200) {
          clearInterval(poll);
          resolve();
        }
      }).on('error', () => {}); // Server not ready yet
    }, 500);
  });
}

// ── Stop server ─────────────────────────────────────────────────────
function stopServer() {
  if (serverProcess) {
    console.log('Stopping server...');
    serverProcess.kill('SIGTERM');
    serverProcess = null;
  }
}

// ── Create Window ───────────────────────────────────────────────────
function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1280,
    height: 800,
    minWidth: 960,
    minHeight: 600,
    title: 'Life Simulator',
    icon: path.join(__dirname, '..', 'web', 'assets', 'icon.png'),
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
    },
    backgroundColor: '#1a1a2e',
    show: false, // Show after content loads
  });

  mainWindow.loadURL(SERVER_URL);

  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
    mainWindow.focus();
  });

  mainWindow.on('closed', () => {
    mainWindow = null;
  });

  // DevTools in development
  if (process.argv.includes('--dev')) {
    mainWindow.webContents.openDevTools();
  }
}

// ── App Lifecycle ───────────────────────────────────────────────────
app.whenReady().then(async () => {
  try {
    console.log('Starting Life Simulator...');
    await startServer();
    console.log('Server ready, opening window...');
    createWindow();
  } catch (err) {
    console.error('Failed to start:', err);
    dialog.showErrorBox(
      'Life Simulator Error',
      `Failed to start the game server:\n\n${err.message}\n\nPlease make sure Python and FastAPI are installed.`
    );
    app.quit();
  }
});

app.on('window-all-closed', () => {
  stopServer();
  app.quit();
});

app.on('before-quit', () => {
  stopServer();
});

app.on('activate', () => {
  if (mainWindow === null) {
    createWindow();
  }
});
