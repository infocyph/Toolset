# Toolset

Welcome to **Toolset**, a collection of essential scripts for managing Docker environments and PHP versions with ease. This repository includes powerful tools like `dockex` and `phpx` to automate various tasks, from Docker container management to switching PHP versions and managing extensions.

## Table of Contents
- [Installation](#installation)
- [Scripts Overview](#scripts-overview)
  - [dockex](#dockex)
  - [phpx](#phpx)
- [Usage](#usage)
  - [dockex Commands](#dockex-commands)
  - [phpx Commands](#phpx-commands)
- [Contributing](#contributing)
- [License](#license)

## Installation

To start using the **Toolset**, clone this repository to your local machine:

```bash
git clone https://github.com/abmmhasan/Toolset.git
```

### Requirements
- Docker
- PHP CLI
- Bash

## Scripts Overview

### dockex
`dockex` is a Docker utility script designed to streamline container and service management. It automates tasks like starting, stopping, and managing Docker containers, networks, and volumes.

#### Key Features:
- Manage Docker containers and images
- Inspect and manipulate volumes and networks
- Benchmark container performance
- Simplified syntax for common Docker tasks

### phpx
`phpx` is a PHP version management script that makes switching between PHP versions easy, installing new extensions, and managing PHP configurations.

#### Key Features:
- Switch between multiple PHP versions
- Install and manage PHP extensions
- Modify PHP-FPM and CLI configurations
- Automate composer installations

## Usage

### dockex Commands

```bash
dockex [command] [options]
```

#### Help

To see all available commands:

```bash
dockex --help
```

#### Available Commands:
- `dockex start <service>`: Start a specific Docker service.
- `dockex stop <service>`: Stop a running Docker service.
- `dockex restart <service>`: Restart a Docker service.
- `dockex list`: List all running containers and services.
- `dockex clean`: Remove all stopped containers, unused networks, and dangling images.
- `dockex benchmark`: Benchmark container performance and view resource usage statistics.

For detailed options and arguments, refer to the in-script help section by running `dockex --help`.

### phpx Commands

```bash
phpx [command] [options]
```

#### Help

To see all available commands:

```bash
phpx --help
```

#### Available Commands:
- `phpx switch <version>`: Switch between PHP versions (CLI and FPM). If the version is not installed, the script prompts for installation.
- `phpx ext <version>`: Manage PHP extensions. View installed extensions, and select new extensions to install.
- `phpx install composer`: Install Composer globally if not already installed, and update it if it is.
- `phpx install <extension>`: Install one or multiple PHP extensions using PECL.

For more information, use the `phpx --help` command to view a complete list of features and options.

## Contributing

We welcome contributions! Feel free to submit issues, request new features, or submit pull requests to enhance **Toolset**. Follow the [GitHub Flow](https://guides.github.com/introduction/flow/) for contributions.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
