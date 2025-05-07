# Publishing CareerMate on Uptodown

This guide provides step-by-step instructions for publishing the CareerMate desktop application on Uptodown.

## Preparing Your App for Uptodown

1. **Build the application packages**:
   ```bash
   cd /Users/Sakshi/PycharmProjects/CareerMate/desktop
   ./prepare-for-uptodown.sh
   ```
   This will create a directory called `uptodown` with all the necessary files.

2. **Add screenshots**:
   - Create screenshots of your application showing key features
   - Save them in the `uptodown/screenshots` directory
   - Recommended: Include at least 3-5 screenshots showing different features

## Creating an Account on Uptodown

1. Go to the [Uptodown Developers Console](https://developers.uptodown.com/)
2. Register for a new account or log in if you already have one
3. Complete your developer profile with accurate information

## Publishing Your App

1. **Add a new app**:
   - In the Developers Console, click on "Add new app"
   - Fill in the basic information about CareerMate

2. **App Details**:
   - **Name**: CareerMate
   - **Description**: Use the content from README.md
   - **Category**: Education or Productivity
   - **Tags**: career, resume, job search, interview preparation, AI assistant
   - **Website**: Your website or GitHub repository URL

3. **Upload Files**:
   - Upload the installer files from the `uptodown` directory
   - Make sure to upload versions for all supported platforms (Windows, macOS, Linux)

4. **Add Screenshots**:
   - Upload the screenshots from the `uptodown/screenshots` directory
   - Add captions explaining what each screenshot shows

5. **Version Information**:
   - Version: 1.0.0
   - Release notes: "Initial release of CareerMate Desktop Application"

6. **Submit for Review**:
   - Review all information for accuracy
   - Submit your app for review by the Uptodown team

## After Publishing

1. **Monitor your app's status** in the Developers Console
2. **Respond promptly** to any feedback from the Uptodown review team
3. **Update your app** when new versions are available

## Support

For any issues with the publishing process, contact Uptodown support at:
- [Uptodown Support](https://support.uptodown.com/)

For issues specific to CareerMate, contact:
- Email: adhyottech@gmail.com