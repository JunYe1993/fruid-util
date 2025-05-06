# fruid-util

FRU Data Parser and Modifier

## Overview

This Python script, `fruid-util.py`, is a tool for parsing, modifying, and rebuilding Field Replaceable Unit (FRU) data. It works with FRU binary files, allowing users to read existing FRU data, modify specific fields, and create new FRU files.

## Features

- Parse existing FRU binary files
- JSON output of parsed FRU data
- Modify FRU fields including chassis, board, and product information
- Rebuild FRU binary data after modifications
- Create new FRU files

## Requirements

- Python 3.8+
- No external dependencies required

## Usage
```
usage: python3 fruid-util.py fru_file [-h] [-v] [-m] [field options]

FRU Data Parser and Modifier

positional arguments:
  fru_file       path to the FRU file

options:
  -h, --help     show this help message and exit
  -v, --version  show program's version number and exit
  -m, --modify   modify fields

field options:
  --CPN CPN      modify Chassis Part Number
  --CSN CSN      modify Chassis Serial Number
  --CCD1 CCD1    modify Chassis Custom Data 1
  --CCD2 CCD2    modify Chassis Custom Data 2
  --CCD3 CCD3    modify Chassis Custom Data 3
  --BMD BMD      modify Board Mfg Date
  --BM BM        modify Board Mfg
  --BP BP        modify Board Product
  --BSN BSN      modify Board Serial
  --BPN BPN      modify Board Part Number
  --BFI BFI      modify Board FRU ID
  --BCD1 BCD1    modify Board Custom Data 1
  --BCD2 BCD2    modify Board Custom Data 2
  --BCD3 BCD3    modify Board Custom Data 3
  --BCD4 BCD4    modify Board Custom Data 4
  --BCD5 BCD5    modify Board Custom Data 5
  --BCD6 BCD6    modify Board Custom Data 6
  --PM PM        modify Product Manufacturer
  --PN PN        modify Product Name
  --PPN PPN      modify Product Part Number
  --PV PV        modify Product Version
  --PSN PSN      modify Product Serial
  --PAT PAT      modify Product Asset Tag
  --PFI PFI      modify Product FRU ID
  --PCD1 PCD1    modify Product Custom Data 1
  --PCD2 PCD2    modify Product Custom Data 2
  --PCD3 PCD3    modify Product Custom Data 3
  --PCD4 PCD4    modify Product Custom Data 4
  --PCD5 PCD5    modify Product Custom Data 5
  --PCD6 PCD6    modify Product Custom Data 6

Examples:
  Display FRU data:
    python3 fruid-util.py fru_file.bin

  Modify Chassis Serial Number:
    python3 fruid-util.py fru_file.bin -m --CSN "NEW_SERIAL_NUMBER"

  Modify multiple fields:
    python3 fruid-util.py fru_file.bin -m --CSN "NEW_SERIAL" --BPN "NEW_PART_NUMBER" --PSN "NEW_PRODUCT_SERIAL"
```
