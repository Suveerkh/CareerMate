const { app, BrowserWindow, ipcMain, dialog, Menu } = require('electron');
const path = require('path');
const { PythonShell } = require('python-shell');
const isDev = require('electron-is-dev');
const fs = require('fs');
const axios = require('axios');
const { autoUpdater } = require('electron-updater');
const log = require('electron-log');

// Keep a global reference of the window object to avoid garbage collection
let mainWindow;
let pythonProcess = null;
let serverRunning = false;
let serverPort = 5001;
// Load configuration
const configPath = path.join(app.getPath('userData'), 'config.json');
let config = {
  serverUrl: 'https://careermate-actual-server.com', // Default server URL
  useLocalServer: true // Whether to use local server as fallback
};

// Try to load config from file
try {
  if (fs.existsSync(configPath)) {
    const configData = fs.readFileSync(configPath, 'utf8');
    const loadedConfig = JSON.parse(configData);
    config = { ...config, ...loadedConfig };
    console.log('Loaded configuration:', config);
  } else {
    // Create default config file if it doesn't exist
    fs.writeFileSync(configPath, JSON.stringify(config, null, 2));
    console.log('Created default configuration file');
  }
} catch (error) {
  console.error('Error loading configuration:', error);
}

// Set up server URLs
// Local server as primary option
let localServerUrl = `http://localhost:${serverPort}`;
// Use local server as the default
let serverUrl = localServerUrl;
// Fallback URLs in case the local one doesn't work
const remoteUrls = [
  'http://localhost:5001/careers'
];
let connectionCheckInterval;

// Create application menu
function createAppMenu() {
  const template = [
    {
      label: 'File',
      submenu: [
        { role: 'quit' }
      ]
    },
    {
      label: 'Settings',
      submenu: [
        {
          label: 'Configure Server',
          click: () => {
            // Show dialog to configure server URL
            const result = dialog.showMessageBoxSync(mainWindow, {
              type: 'info',
              title: 'Server Configuration',
              message: 'Enter the URL of your CareerMate server:',
              buttons: ['OK', 'Cancel'],
              defaultId: 0,
              cancelId: 1,
              prompt: true,
              inputValue: config.serverUrl
            });
            
            if (result === 0) {
              const inputValue = dialog.showInputBox({
                title: 'Server URL',
                defaultValue: config.serverUrl
              });
              
              if (inputValue) {
                // Update config
                config.serverUrl = inputValue;
                serverUrl = inputValue;
                
                // Save config to file
                fs.writeFileSync(configPath, JSON.stringify(config, null, 2));
                
                // Restart connection check
                clearInterval(connectionCheckInterval);
                connectionCheckInterval = setInterval(checkServerConnection, 5000);
                
                // Show confirmation
                dialog.showMessageBoxSync(mainWindow, {
                  type: 'info',
                  title: 'Server Configuration',
                  message: `Server URL updated to: ${inputValue}`,
                  buttons: ['OK']
                });
              }
            }
          }
        },
        {
          label: 'Use Local Server',
          type: 'checkbox',
          checked: config.useLocalServer,
          click: (menuItem) => {
            // Update config
            config.useLocalServer = menuItem.checked;
            
            // Save config to file
            fs.writeFileSync(configPath, JSON.stringify(config, null, 2));
            
            // Show confirmation
            dialog.showMessageBoxSync(mainWindow, {
              type: 'info',
              title: 'Server Configuration',
              message: `Local server ${menuItem.checked ? 'enabled' : 'disabled'}`,
              buttons: ['OK']
            });
          }
        }
      ]
    },
    {
      label: 'View',
      submenu: [
        { role: 'reload' },
        { role: 'forceReload' },
        { role: 'toggleDevTools' },
        { type: 'separator' },
        { role: 'resetZoom' },
        { role: 'zoomIn' },
        { role: 'zoomOut' },
        { type: 'separator' },
        { role: 'togglefullscreen' }
      ]
    },
    {
      label: 'Help',
      submenu: [
        {
          label: 'About CareerMate',
          click: () => {
            dialog.showMessageBoxSync(mainWindow, {
              type: 'info',
              title: 'About CareerMate',
              message: 'CareerMate Desktop Application',
              detail: `Version: ${app.getVersion()}\nElectron: ${process.versions.electron}\nChrome: ${process.versions.chrome}\nNode.js: ${process.versions.node}\nV8: ${process.versions.v8}`,
              buttons: ['OK']
            });
          }
        }
      ]
    }
  ];
  
  const menu = Menu.buildFromTemplate(template);
  Menu.setApplicationMenu(menu);
}

// Create the browser window
function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false,
      webSecurity: false, // Needed for local development
      partition: 'persist:careermate' // Use a persistent session to maintain cookies
    },
    icon: path.join(__dirname, 'icons/icon.png')
  });
  
  // Create application menu
  createAppMenu();

  // Check for internet connection
  checkInternetConnection();
  
  // Start the Python Flask server if enabled
  if (config.useLocalServer) {
    startPythonServer();
  } else {
    console.log('Local server is disabled in configuration');
  }
  
  // Set up periodic connection checks to the server
  connectionCheckInterval = setInterval(checkServerConnection, 5000);
  
  // Load the splash screen while server starts
  mainWindow.loadFile(path.join(__dirname, 'splash.html'));
  
  // Open DevTools in development mode
  if (isDev) {
    mainWindow.webContents.openDevTools();
  }
  
  // Handle navigation events
  mainWindow.webContents.on('did-navigate', (event, url) => {
    console.log('Navigation occurred to:', url);
    
    // If navigated to login page after being on another page, the user might have been logged out
    if (url.includes('/login') && serverRunning) {
      console.log('Detected navigation to login page');
    }
    
    // If navigated to careers page, the user is authenticated
    if (url.includes('/careers')) {
      console.log('User is authenticated and on careers page');
    }
  });
  
  mainWindow.on('closed', function () {
    mainWindow = null;
    clearInterval(connectionCheckInterval);
    stopPythonServer();
  });
}

// Start the Python Flask server
function startPythonServer() {
  console.log('Starting Python server...');
  const appPath = isDev 
    ? path.join(__dirname, '..') 
    : path.join(process.resourcesPath, 'app');
  
  console.log('App path:', appPath);
  
  const options = {
    mode: 'text',
    pythonPath: 'python3', // Use system Python 3
    pythonOptions: ['-u'], // Unbuffered output
    scriptPath: appPath,
    args: ['--port', serverPort.toString()]
  };
  
  console.log('Python options:', options);
  
  try {
    console.log('Spawning Python process for app.py...');
    // Use PythonShell.spawn instead of run for better process control
    pythonProcess = new PythonShell('app.py', options);
    
    // Add command line argument for port
    if (options.args && options.args.includes('--port')) {
      const portIndex = options.args.indexOf('--port') + 1;
      console.log(`Using port ${options.args[portIndex]} for server`);
    }
    
    pythonProcess.on('message', function(message) {
      console.log('Python server message:', message);
    });
    
    pythonProcess.on('error', function(err) {
      console.error('Python server error:', err);
      showErrorDialog('Server Error', 'An error occurred with the application server. Please check your Python installation.');
    });
    
    pythonProcess.on('close', function() {
      console.log('Python server process closed');
      serverRunning = false;
    });
    
    console.log('Setting timeout to check server connection in 3 seconds...');
    // Wait for server to start
    setTimeout(checkServerConnection, 3000);
  } catch (error) {
    console.error('Error starting Python process:', error);
    showErrorDialog('Server Error', 'Failed to start the application server.');
  }
}

// Start the main application server
function startMainAppServer() {
  console.log('Starting main application server...');
  
  // Stop the health server first
  stopPythonServer();
  
  const appPath = isDev 
    ? path.join(__dirname, '..') 
    : path.join(process.resourcesPath, 'app');
  
  const options = {
    mode: 'text',
    pythonPath: 'python3', // Use system Python 3
    pythonOptions: ['-u'], // Unbuffered output
    scriptPath: appPath,
    args: ['--port', serverPort.toString()]
  };
  
  try {
    console.log('Spawning Python process for app.py...');
    // Use PythonShell.spawn instead of run for better process control
    pythonProcess = new PythonShell('app.py', options);
    
    pythonProcess.on('message', function(message) {
      console.log('Main app server message:', message);
    });
    
    pythonProcess.on('error', function(err) {
      console.error('Main app server error:', err);
      showErrorDialog('Server Error', 'An error occurred with the main application server.');
    });
    
  } catch (error) {
    console.error('Error starting main app process:', error);
    showErrorDialog('Server Error', 'Failed to start the main application server.');
  }
}

// Stop the Python server when the app closes
function stopPythonServer() {
  if (pythonProcess) {
    // Check if pythonProcess is an array (PythonShell.run returns an array)
    if (Array.isArray(pythonProcess) && pythonProcess.length > 0) {
      pythonProcess.forEach(proc => {
        if (proc && typeof proc.kill === 'function') {
          proc.kill();
        }
      });
    } 
    // If it's a single process object with terminate method
    else if (pythonProcess.terminate) {
      pythonProcess.terminate();
    }
    // If it has childProcess property with kill method
    else if (pythonProcess.childProcess && typeof pythonProcess.childProcess.kill === 'function') {
      pythonProcess.childProcess.kill();
    }
    // Last resort - try to end the process
    else if (typeof pythonProcess.end === 'function') {
      pythonProcess.end();
    }
    
    pythonProcess = null;
    serverRunning = false;
  }
}

// Check if the server is running
async function checkServerConnection() {
  console.log('Checking server connection...');
  
  // Try the local server first
  if (config.useLocalServer) {
    try {
      console.log(`Trying local server: ${localServerUrl}`);
      const response = await axios.get(localServerUrl, { 
        timeout: 5000,
        validateStatus: function (status) {
          // Accept any status code as a valid response
          return status >= 200 && status < 600;
        }
      });
      
      console.log('Local server response:', response.status);
      
      // If we get any response, the server is reachable
      console.log('Local server is running!');
      
      // Update the serverUrl to the local one
      serverUrl = localServerUrl;
      
      if (!serverRunning) {
        console.log('Transitioning from splash to local server...');
        serverRunning = true;
        
        // Load the local server
        mainWindow.loadURL('http://localhost:5001/careers');
      }
      return;
    } catch (localError) {
      console.error('Error connecting to local server:', localError.message);
      console.log('Local server is not accessible, trying remote servers...');
    }
  } else {
    console.log('Local server is disabled in configuration, trying remote servers...');
  }
  
  // If local server failed or is disabled, try the main server
  try {
    console.log(`Trying to connect to main server: ${config.serverUrl}`);
    const response = await axios.get(config.serverUrl, { 
      timeout: 5000,
      validateStatus: function (status) {
        // Accept any status code as a valid response
        return status >= 200 && status < 600;
      }
    });
    
    console.log('Main server response:', response.status);
    
    // If we get any response, the server is reachable
    console.log('Main server is accessible!');
    
    // Update serverUrl to the main one
    serverUrl = config.serverUrl;
    
    if (!serverRunning) {
      console.log('Transitioning from splash to main server...');
      serverRunning = true;
      
      // Load the main server URL
      mainWindow.loadURL('http://localhost:5001/careers');
    }
    return;
  } catch (error) {
    console.error('Error connecting to main server:', error.message);
    
    // If we got a response but with an error status, the server is still reachable
    if (error.response) {
      console.error('Error status:', error.response.status);
      console.log('Main server is reachable but returned an error');
      
      if (!serverRunning) {
        console.log('Transitioning from splash to main server...');
        serverRunning = true;
        
        // Try to load the main page anyway
        mainWindow.loadURL(config.serverUrl);
      }
      return;
    }
    
    // If main server is not accessible, try fallback URLs
    console.log('Main server is not accessible, trying fallback URLs...');
  }
  
  // Try each fallback URL
  for (const url of remoteUrls) {
    try {
      console.log(`Trying fallback URL: ${url}`);
      const response = await axios.get(url, { 
        timeout: 5000,
        validateStatus: function (status) {
          // Accept any status code as a valid response
          return status >= 200 && status < 600;
        }
      });
      
      console.log(`Fallback URL response (${url}):`, response.status);
      
      // If we get any response, the server is reachable
      console.log(`Fallback URL ${url} is accessible!`);
      
      // Update the serverUrl to the one that worked
      serverUrl = url;
      
      if (!serverRunning) {
        console.log('Transitioning from splash to fallback server...');
        serverRunning = true;
        
        // Load the fallback URL
        mainWindow.loadURL(url);
      }
      return;
    } catch (error) {
      console.error(`Error connecting to fallback URL ${url}:`, error.message);
      
      // If we got a response but with an error status, the server is still reachable
      if (error.response) {
        console.error('Error status:', error.response.status);
        console.log(`Fallback URL ${url} is reachable but returned an error`);
        
        // Update the serverUrl to the one that responded
        serverUrl = url;
        
        if (!serverRunning) {
          console.log('Transitioning from splash to fallback server...');
          serverRunning = true;
          
          // Try to load the fallback URL anyway
          mainWindow.loadURL(url);
        }
        return;
      }
    }
  }
  
  // If all servers failed
  if (serverRunning) {
    console.log('All servers were running but now are down, showing offline screen');
    serverRunning = false;
    mainWindow.loadFile(path.join(__dirname, 'offline.html'));
  } else {
    console.log('All servers are down, showing no-connection screen');
    mainWindow.loadFile(path.join(__dirname, 'no-connection.html'));
    
    // Start the local server as a last resort if enabled
    if (!pythonProcess && config.useLocalServer) {
      console.log('Starting local server as fallback...');
      startPythonServer();
    } else if (!config.useLocalServer) {
      console.log('Local server is disabled in configuration');
    }
  }
}

// Check for internet connection
async function checkInternetConnection() {
  try {
    console.log('Checking internet connection...');
    // Try multiple reliable sites to check for internet connectivity
    const sites = [
      'https://www.google.com',
      'https://www.cloudflare.com',
      'https://www.apple.com',
      'https://www.microsoft.com'
    ];
    
    for (const site of sites) {
      try {
        console.log(`Trying to connect to ${site}...`);
        const response = await axios.get(site, { timeout: 5000 });
        if (response.status === 200) {
          console.log('Internet connection confirmed!');
          return true;
        }
      } catch (error) {
        console.error(`Error connecting to ${site}:`, error.message);
      }
    }
    
    console.error('No internet connection available');
    return false;
  } catch (error) {
    console.error('Error checking internet connection:', error);
    return false;
  }
}

// Show error dialog
function showErrorDialog(title, message) {
  if (mainWindow) {
    dialog.showMessageBox(mainWindow, {
      type: 'error',
      title: title,
      message: message,
      buttons: ['OK']
    });
  } else {
    console.error(`${title}: ${message}`);
  }
}

// Handle app ready event
app.on('ready', () => {
  createWindow();
  
  // Set up auto-updater
  if (!isDev) {
    setupAutoUpdater();
  }
});

// Set up auto-updater
function setupAutoUpdater() {
  log.transports.file.level = 'info';
  autoUpdater.logger = log;
  
  autoUpdater.on('checking-for-update', () => {
    console.log('Checking for updates...');
  });
  
  autoUpdater.on('update-available', (info) => {
    console.log('Update available:', info);
    dialog.showMessageBox(mainWindow, {
      type: 'info',
      title: 'Update Available',
      message: `A new version (${info.version}) is available and will be downloaded in the background.`,
      buttons: ['OK']
    });
  });
  
  autoUpdater.on('update-not-available', (info) => {
    console.log('No updates available:', info);
  });
  
  autoUpdater.on('error', (err) => {
    console.error('Error in auto-updater:', err);
  });
  
  autoUpdater.on('download-progress', (progressObj) => {
    console.log(`Download progress: ${progressObj.percent}%`);
  });
  
  autoUpdater.on('update-downloaded', (info) => {
    console.log('Update downloaded:', info);
    dialog.showMessageBox(mainWindow, {
      type: 'info',
      title: 'Update Ready',
      message: 'A new version has been downloaded. Restart the application to apply the updates.',
      buttons: ['Restart', 'Later']
    }).then((returnValue) => {
      if (returnValue.response === 0) {
        autoUpdater.quitAndInstall();
      }
    });
  });
  
  // Check for updates
  autoUpdater.checkForUpdatesAndNotify();
}

// Quit when all windows are closed
app.on('window-all-closed', function () {
  // On macOS it is common for applications and their menu bar
  // to stay active until the user quits explicitly with Cmd + Q
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', function () {
  // On macOS it's common to re-create a window in the app when the
  // dock icon is clicked and there are no other windows open.
  if (mainWindow === null) {
    createWindow();
  }
});

// Handle IPC messages from renderer process
ipcMain.on('restart-server', () => {
  console.log('Received request to restart server');
  stopPythonServer();
  startPythonServer();
});

ipcMain.on('check-connection', () => {
  console.log('Received request to check connection');
  checkServerConnection();
});

// Handle uncaught exceptions
process.on('uncaughtException', (error) => {
  console.error('Uncaught exception:', error);
  log.error('Uncaught exception:', error);
  
  if (mainWindow) {
    dialog.showMessageBox(mainWindow, {
      type: 'error',
      title: 'Application Error',
      message: 'An unexpected error occurred.',
      detail: error.toString(),
      buttons: ['OK']
    });
  }
});