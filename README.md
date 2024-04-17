# winmsifix
Small Python script to fix the "Network resource unavailable" error when installing packages

## Warning!
This script takes on quite an aggressive approach to fix the error; as a result of it, you will probably be left with some leftover files in your system. Though, if you can sacrifice that, it **will** save you from a massive headache.

## Why?
If you've ever tried to install an MSI installer, or a program that requires one, and you got hit with the aforementioned error, you'll know how annoying it is.

This error usually happens after deleting stuff inside of the `C:\Windows\Installer` folder. This is because Windows keeps a local backup of the installer files, to properly keep track of the installed packages as well as being able to repair or uninstall them properly.

When you're low on space, though, people (like me) may delete this folder because it can get pretty huge, pretty quickly. This will corrupt the Windows registry records and cause the annoying aforementioned error.

## What does it do?
This script searches through the registry for all of the installed packages matching a given query, looking up the installer files both from the Windows Installer folder and from the Temp folder.

Any packages that aren't found are put in a temporary list. The script will then ask the user if they wish to delete said programs from the registry, **after taking a backup of them** (it will refuse to proceed if a backup isn't saved).

This will let you re-install any newer version of the MSI for the same program, bypassing the checks Windows put in place.

## Usage
Start an elevated terminal, then run `python main.py` to start it.

The script will prompt you for a search query, after which it'll let you choose whether you want to delete any broken package references from the registry.

## Contributing
Contributions and fixes are welcome! This was botched up quickly in a desperate attempt to install a couple programs I was having issues with, so it may not be great. Feel free to improve it and PR!

## Credits
- [@zeph (me)](https://github.com/ZephyrCodesStuff)