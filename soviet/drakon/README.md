# Drakon Chart Editor

This directory is designated for the Drakon Chart Editor repository.

## About

The Drakon Chart Editor was intended to be added from:
https://github.com/J-Ellette/Drakon-Chart-Editor

## Note

The repository https://github.com/J-Ellette/Drakon-Chart-Editor does not currently exist.
This folder structure has been created to prepare for when the repository is available.

## Adding the Repository

Once the Drakon-Chart-Editor repository is created, it can be added here using:

```bash
# Option 1: As a git submodule (recommended)
# First, remove this README and the empty directory
cd soviet
rm -rf drakon
# Then add the submodule
git submodule add https://github.com/J-Ellette/Drakon-Chart-Editor.git soviet/drakon

# Option 2: Clone the repository contents directly
cd soviet/drakon
rm README.md  # Remove this placeholder README
git clone https://github.com/J-Ellette/Drakon-Chart-Editor.git .
```
