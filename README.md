<div align="center">
  
# Emby-Media-Renamer

<p align="center">
  <a href="https://www.python.org"><img src="https://img.shields.io/badge/Python-3.8+-4B8BBE?style=for-the-badge&logo=python&logoColor=white" alt="Python"/></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" alt="License"/></a>
  <a href="#"><img src="https://img.shields.io/badge/Version-1.0.0-blue?style=for-the-badge" alt="Version"/></a>
  <br/>
  <a href="#"><img src="https://img.shields.io/badge/Platform-Windows%20|%20Linux%20|%20MacOS-lightgrey?style=for-the-badge" alt="Platform"/></a>
  <a href="https://github.com/yourusername/Emby-Media-Renamer/issues"><img src="https://img.shields.io/badge/Maintenance-Active-brightgreen?style=for-the-badge" alt="Maintenance"/></a>
</p>

**Automated Media File Renaming System | Enhancing Media Server Recognition**

</div>

## Overview

Automated media file monitoring and standardized naming tool designed for Emby, Jellyfin, and Plex media servers. This tool automatically monitors specified directories, parses media filenames, and renames them according to standard naming conventions, improving metadata scraping accuracy.

> ⚠️ **Warning**: This project's code was generated with AI assistance. While tested, it may contain errors or security risks. Please use with caution in production environments and thoroughly review the code before deployment.

## Features

Real-time monitoring - Using efficient file system monitoring mechanisms to detect new and modified media files
Intelligent parsing - Powerful parsing algorithms extract key media information from various complex filenames
AI enhancement - Integrated artificial intelligence to handle difficult-to-identify non-standard naming formats
Standardized output - File naming conventions that comply with media server best practices
High stability - Multi-threaded queue system ensures reliability when processing large media libraries

## Installation & Setup

### System Requirements

- Python 3.8 or higher
- Supports Windows, Linux and macOS
- Recommended: 2GB+ RAM (when processing large media libraries)

### Installation Steps

```bash
# Clone repository
git clone https://github.com/yourusername/Emby-Media-Renamer.git

# Enter project directory
cd Emby-Media-Renamer

# Install dependencies
pip install -r requirements.txt
```

### Configuration

Create a `config.json` file in the project root directory:

```json
{
  "monitor_path": "/path/to/media",
  "media_exts": [".mkv", ".mp4", ".avi", ".mov"],
  "recursive": true,
  "log_level": "INFO",
  "ai_enabled": false,
  "ai_api_key": "",
  "ai_endpoint": ""
}
```

## Usage

### Basic Usage

```bash
python monitor.py
```

### Using Custom Configuration

```bash
python monitor.py -c /path/to/custom_config.json
```

### Running as a Service

<details>
<summary>Running as a system service on Linux</summary>

```bash
# Create service file
sudo nano /etc/systemd/system/emby-media-renamer.service

# Add the following content
[Unit]
Description=Emby Media Renamer Service
After=network.target

[Service]
User=your_username
WorkingDirectory=/path/to/Emby-Media-Renamer
ExecStart=/usr/bin/python3 monitor.py
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target

# Enable and start service
sudo systemctl enable emby-media-renamer.service
sudo systemctl start emby-media-renamer.service
```
</details>

## Naming Conventions

| Media Type | Naming Format                                | Example                                      |
|:-------:|----------------------------------------------|----------------------------------------------|
| Movie | `Title(Year) - Resolution.extension`         | `The Matrix(1999) - 4K.mkv`                  |
| TV Show | `Title(Year) - S##E## - Resolution.extension` | `Game of Thrones(2011) - S01E01 - 1080p.mp4` |

> ℹ️ Naming that conforms to this standard maximizes the accuracy of media server metadata scraping.

## Technical Architecture

<div align="center">
  
```
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│  File System    │──→ │  Event Queue     │──→ │ Media Info       │
│  Monitor        │      │  Processor      │      │ Extractor       │
└─────────────────┘      └─────────────────┘      └─────────────────┘
                                                          │
                                                          ↓
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│  File System    │ ←── │  File Renamer    │ ←── │  AI Enhancement │
└─────────────────┘      └─────────────────┘      └─────────────────┘
```

</div>

- Monitoring Layer: Efficient file system event capture based on Watchdog library
- Processing Layer: Thread-safe queue ensures file operation order and stability
- Parsing Layer: Precise regular expression engine extracts media metadata
- AI Layer: Integrated large language model processes complex naming formats
- Execution Layer: Secure file system operations ensure data integrity

## Performance Optimization

- Batch Processing: Smart batching reduces system calls
- File Caching: Avoids reprocessing the same file
- Delayed Processing: Ensures files are completely written before processing
- Low Resource Usage: Maintains extremely low resource consumption even during long-term operation

## Configuration Parameters

| Parameter | Description | Default Value | Required |
|-----|------|-------|:----:|
| `monitor_path` | Media file directory path to monitor | - | ✓ |
| `media_exts` | List of media file extensions to process | [".mkv", ".mp4", ".avi", ...] | |
| `recursive` | Whether to monitor subdirectories recursively | `true` | |
| `log_level` | Log level (DEBUG/INFO/WARNING/ERROR) | `INFO` | |
| `ai_enabled` | Whether to enable AI-assisted parsing | `false` | |
| `ai_api_key` | AI service API key | - | If AI enabled |
| `ai_endpoint` | AI service endpoint URL | - | If AI enabled |

## License

This project is released under the [MIT License](LICENSE).

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=yourusername/Emby-Media-Renamer&type=Date)](https://star-history.com/#yourusername/Emby-Media-Renamer&type=Date)

<div align="center">
<sub>Precise Naming • Perfect Organization • Media Server's Best Assistant</sub>
</div>