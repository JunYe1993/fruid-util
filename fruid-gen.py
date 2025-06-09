import argparse
import openpyxl
import os
import re
import shutil
import subprocess
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

__version__ = "v2025.19.0"

# Set your platform name here
PLATFORM_NAME = "PlatformName"

# Field configuration: (option, [script_types], default_length)
FIELD_CONFIG = {
    "Chassis Part Number": ("CPN", ["M3"], None),
    "Chassis Serial Number": ("CSN", ["M3"], None),
    "Chassis Custom Data 1": ("CCD1", ["M3"], None),
    "Chassis Custom Data 2": ("CCD2", ["M1", "M3"], 12),
    "Chassis Custom Data 3": ("CCD3", ["M3"], None),
    "Board Mfg": ("BM", ["M1", "M3"], None),
    "Board Product": ("BP", ["M1", "M3"], None),
    "Board Serial": ("BSN", ["M1"], 15),
    "Board Part Number": ("BPN", ["M1", "M3"], None),
    "Board FRU ID": ("BFI", ["M1", "M3"], None),
    "Board Custom Data 1": ("BCD1", ["M1", "M3"], None),
    "Board Custom Data 2": ("BCD2", ["M1"], 7),
    "Board Custom Data 3": ("BCD3", ["M1"], 5),
    "Board Custom Data 4": ("BCD4", ["M1", "M3"], None),
    "Board Custom Data 5": ("BCD5", ["M1"], None),
    "Board Custom Data 6": ("BCD6", ["M1"], None),
    "Product Manufacturer": ("PM", ["M1", "M3"], None),
    "Product Name": ("PN", ["M1", "M3"], None),
    "Product Part Number": ("PPN", ["M3"], None),
    "Product Version": ("PV", ["M1", "M3"], None),
    "Product Serial": ("PSN", ["M3"], None),
    "Product Asset Tag": ("PAT", ["M3"], None),
    "Product FRU ID": ("PFI", ["M3"], None),
    "Product Custom Data 1": ("PCD1", ["M3"], None),
    "Product Custom Data 2": ("PCD2", ["M3"], None),
    "Product Custom Data 3": ("PCD3", ["M3"], None),
    "Product Custom Data 4": ("PCD4", ["M3"], None),
    "Product Custom Data 5": ("PCD5", ["M3"], None),
    "Product Custom Data 6": ("PCD6", ["M3"], None),
}


def is_empty_field(value):
    if not isinstance(value, str):
        return False

    # Check for patterns indicating empty data
    empty_keywords = [
        r"\[\s*empty.*?\]",
    ]
    return any(re.search(keyword, value, re.IGNORECASE) for keyword in empty_keywords)


def is_non_displayable_ascii(value):
    if not isinstance(value, str):
        return False
    return any(ord(char) < 32 or ord(char) > 126 for char in value)


# To identify if the field needs input data
def is_dynamic_content(value, stage):
    if not isinstance(value, str):
        return False

    stage_keywords = {
        "M1": r"m1[\s_\n]*(odm[\s_\n]*)?(define|program)",
        "M3": r"m3[\s_\n]*(odm[\s_\n]*)?(define|program)",
    }
    for key, keyword in stage_keywords.items():
        if re.search(keyword, value, re.IGNORECASE):
            if key != stage:
                return None
            return True

    dynamic_keywords = [
        r"odm[\s_\n]*define",
        r"odm[\s_\n]*program",
        r"\[.*?\]",
        r"batch[\s_\n]*id",
    ]
    return any(re.search(keyword, value, re.IGNORECASE) for keyword in dynamic_keywords)


def strip_field_content(value):
    if not isinstance(value, str):
        return value

    # Remove leading and trailing spaces
    value = value.strip()
    # Replace multiple spaces with a single space
    value = re.sub(r"\s+", " ", value)

    return value


def get_version_from_fru_id(fru_fields):
    match = re.search(r"(\d+\.\d+)", fru_fields.get("Board FRU ID", ""))
    if match:
        version = match.group(1).replace(".", "")
        return f"v{version.zfill(3)}"
    return "v000"


def create_release_note(folder_path, version, board_info):
    # Get unique board part numbers while preserving order
    all_board_pns = []
    for pn, _ in board_info["M1"] + board_info["M3"]:
        if pn not in all_board_pns:
            all_board_pns.append(pn)

    ict_section = ""
    if "ICT" in board_info and board_info["ICT"]:
        ict_section = "     iii. ICT: For ICT.\n"
        ict_section += chr(10).join(
            f"        {pn}: {product}" for pn, product in board_info["ICT"]
        )
        ict_section += "\n"

    content = f"""===============================================================
   FRU Release Note {version}
===============================================================
Version: {version}
Date: {datetime.now().strftime('%Y/%m/%d')}
Hardware Platform: {PLATFORM_NAME}

Note:
  1. The utility and scripts for programming FRU on Linux OS (with Python 3.8+)
  2. The scripts of programming FRU for specific boards.
     i. M1: For M1 stage.
{chr(10).join(f'        {pn}.sh: {product}' for pn, product in board_info['M1'])}
     ii. M3: For M3 stage.
{chr(10).join(f'        {pn}.sh: {product}' for pn, product in board_info['M3'])}
{ict_section}
Example procedure:
  1. Programming FRU for M1:
     (1) Change directory to "M1"
     (2) Execute "./<Board_PN>.sh fru.bin" (fru.bin is the output filename)
     (3) scp fru.bin into openbmc
     (4) Execute "dd if=/tmp/fru.bin of=/sys/class/i2c-dev/i2c-xx/device/xx-00xx/eeprom" in openbmc
  2. Programming FRU for M3:
     (1) Move or Copy "M1/fru.bin" to "M3/fru.bin"
     (2) Change directory to "M3"
     (3) Execute "./<Board_PN>.sh fru.bin"
     (4) scp fru.bin into openbmc
     (5) Execute "dd if=/tmp/fru.bin of=/sys/class/i2c-dev/i2c-xx/device/xx-00xx/eeprom" in openbmc

Changed/Added:
  1. FRU files for M1 and M3:
{chr(10).join(f'     ({i+1}) {pn}' for i, pn in enumerate(all_board_pns))}

"""
    with open(os.path.join(folder_path, f"FRU_Release_Note_{version}.txt"), "w") as f:
        f.write(content)


def determine_field_length(field, value):
    # Check for [#..] pattern in the value
    if isinstance(value, str):
        pound_match = re.search(r"\[#(\d+)\]", value)
        if pound_match:
            # Return the numeric value
            return int(pound_match.group(1))

    if field in FIELD_CONFIG and len(FIELD_CONFIG[field]) > 2:
        default_length = FIELD_CONFIG[field][2]
        if default_length is not None:
            return default_length

    return 0


def generate_fru_script_content(fru_fields, script_type, board_pn):
    is_ict = False
    if script_type == "ICT":
        is_ict = True
        script_type = "M1"

    xlsx_line = f'XLSX="${{BIN%.*}}.xlsx"\n' if is_ict else ""
    script_content = (
        "#!/bin/sh\n\n"
        'UTIL=$(dirname "$0")/../fruid-util.py\n'
        "BIN=${1:-fru.bin}\n"
        f"{xlsx_line}\n"
    )

    assignments = []
    read_commands = []
    python_commands = []

    if fru_fields.get("Chassis Type") and (
        not fru_fields.get("Chassis Part Number")
        or script_type not in FIELD_CONFIG["Chassis Part Number"][1]
    ):
        python_commands.append(' --CPN ""')

    for field, config in FIELD_CONFIG.items():
        option = config[0]
        script_types = config[1]
        if script_type not in script_types:
            continue

        value = fru_fields.get(field)
        if not value or is_empty_field(value):
            continue

        dynamic = is_dynamic_content(value, script_type)
        if dynamic is None:
            continue
        if dynamic:
            if is_ict:
                # For ICT, convert manual entry to raw zeros of appropriate length
                length = determine_field_length(field, value)
                if length > 0:
                    zeros = "0 " * length
                    zeros = zeros.strip()  # Remove trailing space
                    assignments.append(f'{option}="{zeros}"')
                    python_commands.append(f' --{option}-raw "${option}"')
                else:
                    # Default to empty string if we can't determine length
                    assignments.append(f'{option}=""')
                    python_commands.append(f' --{option} "${option}"')
            else:
                read_commands.append(f'read -p "{field}: " {option}')
                python_commands.append(f' --{option} "${option}"')
            continue

        if is_non_displayable_ascii(value):
            print(
                f"Warning: Non-displayable content found in '{field}' for {board_pn} ({script_type})"
            )
            continue

        value = strip_field_content(value)
        assignments.append(f'{option}="{value}"')
        python_commands.append(f' --{option} "${option}"')

    script_content += "\n".join(assignments) + "\n\n"
    script_content += "\n".join(read_commands) + "\n"
    if script_type == "M1":
        script_content += 'rm -f "$BIN"\n\n'
    else:
        script_content += "\n"

    script_content += 'python3 "$UTIL" "$BIN" -m \\\n'
    script_content += " \\\n".join(python_commands)
    if script_type == "M3":
        script_content += " \\\n --BMD \"$(date '+%F %H:%M:%S')\"\n"
    else:
        script_content += "\n"

    script_content += '\npython3 "$UTIL" "$BIN"'
    if is_ict:
        script_content += ' -f "$XLSX"'
    script_content += "\n\n"

    return script_content


def generate_fru_scripts(excel_file, ict_mode=False):
    wb = openpyxl.load_workbook(excel_file)
    sheet = wb.active

    # Column A is for field name, so check start from column B
    column_names = {
        cell.column_letter: cell.value
        for cell in sheet[1][1:]
        if cell.value and not sheet.column_dimensions[cell.column_letter].hidden
    }
    columns = {col: name for col, name in column_names.items() if name}
    if not columns:
        print("Error: No valid data columns found in the Excel file.")
        sys.exit(1)

    # Create base directory
    base_dir = os.path.join("build")
    os.makedirs(base_dir, exist_ok=True)

    # Create M1 and M3 directories
    for stage in ["M1", "M3"]:
        os.makedirs(os.path.join(base_dir, stage), exist_ok=True)

    # Create ICT directory
    if ict_mode:
        os.makedirs(os.path.join(base_dir, "ICT"), exist_ok=True)

    # Copy utility files
    for file in ["fruid-util.py", "README.md"]:
        shutil.copy(file, base_dir)

    board_info = defaultdict(list)
    versions = ["v000"]
    script_content_map = {}
    ict_script_content_map = {}

    for col in columns:
        fru_fields = {}
        for row in range(1, sheet.max_row + 1):
            field_name = sheet[f"A{row}"].value
            field_value = sheet[f"{col}{row}"].value
            if field_name and field_value:
                fru_fields[field_name] = field_value

        board_pn = fru_fields.get("Board Part Number", "unknown")
        board_name = strip_field_content(fru_fields.get("Board Product", "unknown"))
        versions.append(get_version_from_fru_id(fru_fields))

        for stage in ["M1", "M3"]:
            key = (board_pn, stage)
            # Store first occurrence of each board+stage combination
            if key not in script_content_map:
                script_content = generate_fru_script_content(
                    fru_fields, stage, board_pn
                )
                script_content_map[key] = {
                    "content": script_content,
                    "board_name": board_name,
                }

        if ict_mode:
            if board_pn not in ict_script_content_map:
                ict_script_content = generate_fru_script_content(
                    fru_fields, "ICT", board_pn
                )
                ict_script_content_map[board_pn] = {
                    "content": ict_script_content,
                    "board_name": board_name,
                }

    # Write all scripts after processing all data
    for (board_pn, stage), data in script_content_map.items():
        output_script = os.path.join(base_dir, stage, f"{board_pn}.sh")
        with open(output_script, "w") as f:
            f.write(data["content"])
        os.chmod(output_script, 0o755)
        board_info[stage].append((board_pn, data["board_name"]))

    # Write ICT scripts and generate bin/xlsx files
    if ict_mode:
        for board_pn, data in ict_script_content_map.items():
            # Create directory for board output files
            board_dir = os.path.join(base_dir, "ICT", board_pn)
            os.makedirs(board_dir, exist_ok=True)

            # Write temporary script directly in ICT directory
            temp_script_path = os.path.join(base_dir, "ICT", f"__{board_pn}.sh")
            with open(temp_script_path, "w") as f:
                f.write(data["content"])
            os.chmod(temp_script_path, 0o755)
            board_info["ICT"].append((board_pn, data["board_name"]))

            # Execute script to generate bin and xlsx files
            bin_path = os.path.join(board_pn, f"{board_pn}.bin")
            subprocess.run(
                [f"./__{board_pn}.sh", bin_path],
                cwd=os.path.join(base_dir, "ICT"),
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            os.remove(temp_script_path)

    # Create release note
    create_release_note(base_dir, max(versions), board_info)

    print(f"Scripts and files generated successfully in {base_dir}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate FRU scripts from Excel data",
        usage="python3 %(prog)s excel_file [-h] [-v] [-i]",
    )
    parser.add_argument(
        "-v", "--version", action="version", version=f"fruid-gen {__version__}"
    )
    parser.add_argument(
        "excel_file",
        nargs="?",
        type=Path,
        default=Path("fruid.xlsx"),
        help="path to the Excel file containing FRU data (default: fruid.xlsx)",
    )
    parser.add_argument(
        "-i",
        "--ict",
        action="store_true",
        help="generate ICT bin files and documents",
    )

    args = parser.parse_args()

    if not os.path.exists(args.excel_file):
        print(f"Error: The specified Excel file '{args.excel_file}' does not exist.")
        sys.exit(1)

    generate_fru_scripts(args.excel_file, args.ict)
