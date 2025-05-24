# Vault - Simple Backup & Restore

> vault.py is the final version. Other files were attempts at making vault more feature-rich.

## Setup

### Prerequisites

- Python installed on your machine.
- A Linux-based operating system (tested on MacOS).

### Steps

1. Clone the repository:

```bash
git clone https://github.com/adnanxsalim/tool-vault.git
```

2. Navigate to the project directory:

```bash
cd tool-vault
```

3. Update the `vault` script to make it executable:

```bash
chmod +x vault.py
```

4. Move the `vault` script to a directory in your PATH, such as `/usr/local/bin`:

```bash
sudo mv vault.py /usr/local/bin/vault
```

## Commands

- ### vault save

Saves the codebase from the specified source path, with the given name.

The codebases are stored in a directory named _Vault Storage_ under the user's home directory.

The directory is created if it does not exist already.

Usage:

```bash
vault save <source_path> <name>
```

Example:

```bash
vault save /path/to/codebase my_project
```

- ### vault load

Loads and pastes the specified codebase from the _Vault Storage_ to the specified destination.

Usage:

```bash
vault load <destination_path> <name>
```

Example:

```bash
vault load /path/to/paste my_project
```

- ### vault list

Lists all the codebases saved in the _Vault Storage_.

Usage:

```bash
vault list
```

- ### vault delete

Deletes the specified codebase from the _Vault Storage_.

Usage:

```bash
vault delete <name>
```

Example:

```bash
vault delete my_project
```

- ### vault help

Displays help information for the CLI tool.

Usage:

```bash
vault --help
```

---

Full documentation available at [my website](https://adnansal.im/work/tool-vault).