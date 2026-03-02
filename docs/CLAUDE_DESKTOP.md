# Claude Desktop Installation Guide

This guide provides step-by-step instructions for installing Claude Desktop on your computer.

## Table of Contents

- [System Requirements](#system-requirements)
- [Installation Steps](#installation-steps)
  - [Windows](#windows)
  - [macOS](#macos)
  - [Linux](#linux)
- [Initial Setup](#initial-setup)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)

## System Requirements

### Minimum Requirements

- **RAM**: 4 GB minimum (8 GB recommended)
- **Storage**: 500 MB free disk space
- **Internet**: Active internet connection required
- **Display**: 1024x768 resolution minimum

### Supported Operating Systems

- Windows 10 or later (64-bit)
- macOS 11 (Big Sur) or later
- Linux (Ubuntu 18.04 or later, or equivalent)

## Installation Steps

### Windows

1. **Download Claude Desktop**
   - Visit [claude.ai](https://claude.ai)
   - Click on the "Download Desktop" button
   - Download the `.exe` installer for Windows

2. **Run the Installer**
   - Locate the downloaded `.exe` file (usually in Downloads folder)
   - Double-click to launch the installer
   - Accept the User Account Control (UAC) prompt if prompted

3. **Follow Installation Wizard**
   - Accept the license agreement
   - Choose installation location (default is recommended)
   - Select whether to create a Start Menu shortcut
   - Click "Install" and wait for completion

4. **Launch Claude Desktop**
   - Click "Finish" when installation completes
   - Claude Desktop will launch automatically
   - Alternatively, find Claude in the Start Menu and click to open

### macOS

1. **Download Claude Desktop**
   - Visit [claude.ai](https://claude.ai)
   - Click on the "Download Desktop" button
   - Download the `.dmg` file for macOS

2. **Install from DMG**
   - Locate the downloaded `.dmg` file in Downloads
   - Double-click to mount the disk image
   - Drag the Claude icon to the Applications folder
   - Wait for the copy process to complete

3. **Launch Claude Desktop**
   - Open Applications folder
   - Find and double-click "Claude" application
   - Grant any necessary permissions when prompted
   - Accept security permissions from macOS

### Linux

1. **Download Claude Desktop**
   - Visit [claude.ai](https://claude.ai)
   - Follow the instructions for Linux installation (usually involves downloading a `.deb` or `.AppImage` file)

## Initial Setup

1. **Sign In or Create Account**
   - When Claude Desktop opens, you'll be prompted to sign in
   - Use your Anthropic account credentials or create a new account
   - If you don't have one, click "Sign Up" to create an account

2. **Enable Notifications (Optional)**
   - You may be prompted to enable desktop notifications
   - Click "Allow" or "Skip" based on your preference

3. **Configure Preferences**
   - Click the settings icon (gear icon) in the top-right corner
   - Adjust theme (Light/Dark/Auto)
   - Set font size and zoom level
   - Configure notification settings

## Configuration

### MCP (Model Context Protocol) Setup

If you're using MCP servers with Claude Desktop:

1. **Locate Configuration File**
   - Windows: `%APPDATA%\Claude\config.json`
   - macOS: `~/Library/Application Support/Claude/config.json`
   - Linux: `~/.config/Claude/config.json`

2. **Edit Configuration**
   - Open the config file in a text editor
   - Add your MCP server configurations
   - Restart Claude Desktop to apply changes

### Example MCP Configuration

```json
{
  "mcpServers": {
    "your-server-name": {
      "command": "python",
      "args": ["/path/to/your/server.py"],
      "disabled": false
    }
  }
}
```

## Troubleshooting

### Claude Won't Launch

#### Solution 1: Restart Your Computer

1. Close any Claude windows
2. Restart your computer
3. Launch Claude again

#### Solution 2: Reinstall Claude

- Uninstall Claude completely
- Restart your computer
- Download and reinstall the latest version

#### Solution 3: Clear Cache

- Windows: Delete `%LOCALAPPDATA%\Claude` folder
- macOS: Delete `~/Library/Caches/Claude` folder
- Linux: Delete `~/.cache/Claude` folder
- Restart Claude

### Login Issues

- Ensure you have an active internet connection
- Try clearing your browser cookies if sign-in fails
- If you forgot your password, use "Forgot Password" on the sign-in screen
- Contact Anthropic support if issues persist

### Performance Issues

- Close unnecessary applications running in background
- Ensure your system meets minimum requirements
- Check available disk space (needs at least 500 MB free)
- Try disabling hardware acceleration in settings

### MCP Server Connection Issues

- Verify the MCP server is running and accessible
- Check the configuration file syntax (must be valid JSON)
- Review server logs for error messages
- Ensure file paths in config are absolute paths

## Getting Help

- Visit the [Anthropic Help Center](https://support.anthropic.com)
- Check [Claude Documentation](https://docs.anthropic.com)
- Contact support through the Claude Desktop help menu

## Additional Resources

- [MCP Documentation](https://modelcontextprotocol.io)
- [Claude API Documentation](https://docs.anthropic.com/claude/reference)
- [Community Forum](https://discuss.anthropic.com)
