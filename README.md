# Visual Plugin for NVIDIA G-Assist

Transform your G-Assist experience with real-time Visual description!

## What Can It Do?
- Ask any question about the screen

## Before You Start
Make sure you have:
- Windows PC
- Python 3.6 or higher installed
- A replicate account
- NVIDIA G-Assist installed

## Installation Guide

### Step 1: Get the Files
```bash
git clone https://github.com/eletroswing/visual-g-assist-plugin visual
cd visual
```
This downloads all the necessary files to your computer.

### Step 2: Set up your Replicate Api Key
- Register an api. Follow directions here: https://replicate.com/account/api-tokens
- Copy Api Key and paste to the `REPLICATE_KEY` value in the `config.json file` 

### Step 3: Setup and Build
1. Run the setup script:
```bash
setup.bat
```
This installs all required Python packages.

2. Run the build script:
```bash
build.bat
```
This creates the executable and prepares all necessary files.

### Step 4: Install the Plugin
1. Navigate to the `dist` folder created by the build script
2. Copy the `visual` folder to:
```bash
%PROGRAMDATA%\NVIDIA Corporation\nvtopps\rise\plugins
```
💡 **Tip**: Make sure all files are copied, including:
- The executable
- manifest.json
- config.json (Make sure you've updated this with your Replicate credentials)

## How to Use
Once everything is set up, you can ask questions about the screen through simple chat commands.

Try these commands:
- "Hey Visual, what program is open?"
- "How many windows are open?"

## Troubleshooting Tips
### Logging
The plugin logs all activity to:
```
%USERPROFILE%\visual.log
```
Check this file for detailed error messages and debugging information.
