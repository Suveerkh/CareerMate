# CareerMate

CareerMate is a career guidance platform that helps students and graduates explore career options based on their education level and interests.

## Desktop Application

CareerMate is available as a desktop application for Windows, macOS, and Linux. The desktop app provides a seamless experience with automatic updates and offline capabilities.

### Running the Desktop Application in Development Mode

1. Make sure you have Node.js and npm installed on your system.

2. Navigate to the desktop directory:
   ```bash
   cd desktop
   ```

3. Install dependencies:
   ```bash
   npm install
   ```

4. Create application icons:
   ```bash
   ./create-icons.sh
   ```

5. Start the application:
   ```bash
   npm start
   ```

### Building the Desktop Application for Distribution

#### For macOS:
```bash
cd desktop
npm run package-mac
```

#### For Windows:
```bash
cd desktop
npm run package-win
```

#### For Linux:
```bash
cd desktop
npm run package-linux
```

The packaged applications will be available in the `dist` directory.

### Publishing Updates

When you want to release a new version with updates:

1. Update your application code (Flask app, templates, etc.)

2. Update the version number in `desktop/package.json`

3. Build and publish the update:
   ```bash
   cd desktop
   npm run publish
   ```

## Web Application Deployment

### Local Development

To run the application locally:

1. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Create a .env file with the required environment variables.

4. Run the application:
   ```
   python app.py
   ```

The application will be available at http://localhost:5001.