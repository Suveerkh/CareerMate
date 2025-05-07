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
// Use the actual CareerMate server URL from config
let serverUrl = config.serverUrl;
// Fallback URLs in case the main one doesn't work
const remoteUrls = [
  'https://careermate.com',
  'https://www.careermate.com',
  'https://app.careermate.com',
  'https://careermate.herokuapp.com'
];
// Local server as last resort
let localServerUrl = `http://localhost:${serverPort}`;
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
    pythonPath: 'python', // Use system Python
    pythonOptions: ['-u'], // Unbuffered output
    scriptPath: appPath,
    args: ['--port', serverPort.toString()]
  };
  
  console.log('Python options:', options);
  
  try {
    console.log('Spawning Python process for test_server.py...');
    // Use PythonShell.spawn instead of run for better process control
    pythonProcess = new PythonShell('test_server.py', options);
    
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
    pythonPath: 'python', // Use system Python
    pythonOptions: ['-u'], // Unbuffered output
    scriptPath: appPath,
    args: ['--port', serverPort.toString()]
  };
  
  try {
    console.log('Spawning Python process for test_server.py...');
    // Use PythonShell.spawn instead of run for better process control
    pythonProcess = new PythonShell('test_server.py', options);
    
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
  
  // Try the main server first
  try {
    console.log(`Trying to connect to main server: ${serverUrl}`);
    const response = await axios.get(serverUrl, { 
      timeout: 5000,
      validateStatus: function (status) {
        // Accept any status code as a valid response
        return status >= 200 && status < 600;
      }
    });
    
    console.log('Main server response:', response.status);
    
    // If we get any response, the server is reachable
    console.log('Main server is accessible!');
    if (!serverRunning) {
      console.log('Transitioning from splash to main server...');
      serverRunning = true;
      
      // Load the main server URL
      mainWindow.loadURL(serverUrl);
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
        mainWindow.loadURL(serverUrl);
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
  
  // If all remote servers failed and local server is enabled, try it as a last resort
  if (config.useLocalServer) {
    try {
      console.log(`Trying local server: ${localServerUrl}`);
      const response = await axios.get(localServerUrl, { timeout: 2000 });
      console.log('Local server response:', response.status);
      
      if (response.status === 200) {
        console.log('Local server is running!');
        if (!serverRunning) {
          console.log('Transitioning from splash to local server...');
          serverRunning = true;
          
          // Load the local server
          mainWindow.loadURL(localServerUrl);
        }
        return;
      }
    } catch (localError) {
      console.error('Error connecting to local server:', localError.message);
    }
  } else {
    console.log('Local server is disabled in configuration');
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
      'https://www.microsoft.com',
      'https://www.amazon.com'
    ];
    
    // Try each site until one succeeds
    for (const site of sites) {
      try {
        console.log(`Trying to connect to ${site}...`);
        const response = await axios.get(site, { 
          timeout: 5000,
          validateStatus: function (status) {
            // Accept any status code as a valid response
            return status >= 200 && status < 600;
          }
        });
        
        if (response.status >= 200 && response.status < 600) {
          console.log('Internet connection confirmed!');
          // Internet is connected, continue loading
          return true;
        }
      } catch (siteError) {
        console.error(`Failed to connect to ${site}:`, siteError.message);
        // Continue to the next site
      }
    }
    
    // If we get here, all sites failed
    throw new Error('All connectivity checks failed');
  } catch (error) {
    console.error('Internet connection check failed:', error.message);
    
    // Don't block the app from starting, just log the error
    // We'll still try to connect to our servers anyway
    return false;
  }
}

// Check if user is authenticated
async function checkAuthStatus() {
  try {
    // Try to access a protected endpoint that requires authentication
    // We'll use the /careers endpoint which should redirect to login if not authenticated
    console.log('Checking authentication status...');
    
    // First try to access the careers page
    let careersUrl = `${serverUrl}/careers`;
    console.log(`Trying to access: ${careersUrl}`);
    
    // Make a request with { withCredentials: true } to send cookies
    const response = await axios.get(careersUrl, { 
      withCredentials: true,
      maxRedirects: 0,  // Don't follow redirects
      validateStatus: status => status >= 200 && status < 600  // Accept any status code
    });
    
    console.log('Auth check response:', response.status);
    
    if (response.status === 200) {
      // User is authenticated, load the careers page
      console.log('User is authenticated, loading careers page');
      mainWindow.loadURL(careersUrl);
    } else if (response.status === 302 || response.status === 303) {
      // Redirect indicates user is not authenticated
      console.log('Redirect detected, user is not authenticated');
      mainWindow.loadURL(`${serverUrl}/login`);
    } else {
      // Some other status code, default to the main site
      console.log('Unexpected status code, defaulting to main site');
      mainWindow.loadURL(serverUrl);
    }
  } catch (error) {
    console.error('Error checking authentication:', error.message);
    
    // Try a different approach - just load the main URL and let the server handle redirection
    console.log('Falling back to loading the main URL');
    mainWindow.loadURL(serverUrl);
  }
}

// Show error dialog
function showErrorDialog(title, message) {
  dialog.showErrorBox(title, message);
}

// Clear user session and redirect to login page
function clearUserSession() {
  if (mainWindow) {
    // Clear cookies and storage
    const session = mainWindow.webContents.session;
    
    // Show a loading message
    mainWindow.loadFile(path.join(__dirname, 'splash.html'));
    
    // Clear all cookies
    session.clearStorageData({ storages: ['cookies'] })
      .then(() => {
        console.log('Cookies cleared successfully');
        // Redirect to login page
        mainWindow.loadURL(`${serverUrl}/login`);
      })
      .catch(error => {
        console.error('Error clearing cookies:', error);
        // Still try to redirect to login page
        mainWindow.loadURL(`${serverUrl}/login`);
      });
  }
}

// Configure logging
log.transports.file.level = 'info';
autoUpdater.logger = log;

// Auto-updater events
autoUpdater.on('checking-for-update', () => {
  log.info('Checking for update...');
});

autoUpdater.on('update-available', (info) => {
  log.info('Update available:', info);
  dialog.showMessageBox({
    type: 'info',
    title: 'Update Available',
    message: `A new version (${info.version}) of CareerMate is available. It will be downloaded in the background.`,
    buttons: ['OK']
  });
});

autoUpdater.on('update-not-available', (info) => {
  log.info('Update not available:', info);
});

autoUpdater.on('error', (err) => {
  log.error('Error in auto-updater:', err);
});

autoUpdater.on('download-progress', (progressObj) => {
  let logMessage = `Download speed: ${progressObj.bytesPerSecond} - Downloaded ${progressObj.percent}% (${progressObj.transferred}/${progressObj.total})`;
  log.info(logMessage);
  
  if (mainWindow) {
    mainWindow.webContents.send('update-progress', progressObj);
  }
});

autoUpdater.on('update-downloaded', (info) => {
  log.info('Update downloaded:', info);
  
  dialog.showMessageBox({
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

// Create application menu with update option
function createMenu() {
  const template = [
    {
      label: 'File',
      submenu: [
        {
          label: 'Log Out',
          click: () => {
            clearUserSession();
          }
        },
        { type: 'separator' },
        { role: 'quit' }
      ]
    },
    {
      label: 'Edit',
      submenu: [
        { role: 'undo' },
        { role: 'redo' },
        { type: 'separator' },
        { role: 'cut' },
        { role: 'copy' },
        { role: 'paste' }
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
          label: 'Check for Updates',
          click: () => {
            autoUpdater.checkForUpdatesAndNotify();
          }
        },
        {
          label: 'About CareerMate',
          click: () => {
            dialog.showMessageBox({
              title: 'About CareerMate',
              message: 'CareerMate Desktop App',
              detail: `Version: ${app.getVersion()}\nDeveloped by: Adhyot Tech\nEmail: adhyottech@gmail.com`,
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

// Create window when Electron is ready
app.whenReady().then(() => {
  createWindow();
  createMenu();
  
  // Check for updates after app is ready (but not in development)
  if (!isDev) {
    autoUpdater.checkForUpdatesAndNotify();
    
    // Check for updates every 6 hours
    setInterval(() => {
      autoUpdater.checkForUpdatesAndNotify();
    }, 6 * 60 * 60 * 1000);
  }
});

// Quit when all windows are closed
app.on('window-all-closed', function () {
  if (process.platform !== 'darwin') app.quit();
});

app.on('activate', function () {
  if (mainWindow === null) createWindow();
});

// Clean up before quitting
app.on('before-quit', () => {
  stopPythonServer();
});

// Handle IPC messages from renderer
ipcMain.on('restart-server', () => {
  stopPythonServer();
  startPythonServer();
});

ipcMain.on('check-connection', () => {
  checkInternetConnection();
});

ipcMain.on('check-for-updates', () => {
  autoUpdater.checkForUpdatesAndNotify();
});