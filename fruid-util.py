import struct
from datetime import datetime, timedelta
import argparse
import json
from typing import Dict, Any, List, Union
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import logging
import sys

__version__ = "v2025.17.0"

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


# FRU field display configuration
SHOW_VALUE = 1
SHOW_XX = 2


class FieldMapping(Enum):
    CPN = ("chassis", "Chassis Part Number", SHOW_VALUE, None)
    CSN = ("chassis", "Chassis Serial Number", SHOW_XX, None)
    CCD1 = ("chassis", "Chassis Custom Data 1", SHOW_XX, None)
    CCD2 = ("chassis", "Chassis Custom Data 2", SHOW_XX, None)
    CCD3 = ("chassis", "Chassis Custom Data 3", SHOW_XX, None)
    CCD4 = ("chassis", "Chassis Custom Data 4", SHOW_XX, None)
    CCD5 = ("chassis", "Chassis Custom Data 5", SHOW_XX, None)
    CCD6 = ("chassis", "Chassis Custom Data 6", SHOW_XX, None)
    CCD7 = ("chassis", "Chassis Custom Data 7", SHOW_XX, None)
    CCD8 = ("chassis", "Chassis Custom Data 8", SHOW_XX, None)
    CCD9 = ("chassis", "Chassis Custom Data 9", SHOW_XX, None)
    CCD10 = ("chassis", "Chassis Custom Data 10", SHOW_XX, None)
    CCD11 = ("chassis", "Chassis Custom Data 11", SHOW_XX, None)
    CCD12 = ("chassis", "Chassis Custom Data 12", SHOW_XX, None)
    CCD13 = ("chassis", "Chassis Custom Data 13", SHOW_XX, None)
    CCD14 = ("chassis", "Chassis Custom Data 14", SHOW_XX, None)
    CCD15 = ("chassis", "Chassis Custom Data 15", SHOW_XX, None)
    CCD16 = ("chassis", "Chassis Custom Data 16", SHOW_XX, None)
    CCD17 = ("chassis", "Chassis Custom Data 17", SHOW_XX, None)
    CCD18 = ("chassis", "Chassis Custom Data 18", SHOW_XX, None)
    CCD19 = ("chassis", "Chassis Custom Data 19", SHOW_XX, None)
    CCD20 = ("chassis", "Chassis Custom Data 20", SHOW_XX, None)
    CCD21 = ("chassis", "Chassis Custom Data 21", SHOW_XX, None)
    CCD22 = ("chassis", "Chassis Custom Data 22", SHOW_XX, None)
    CCD23 = ("chassis", "Chassis Custom Data 23", SHOW_XX, None)
    CCD24 = ("chassis", "Chassis Custom Data 24", SHOW_XX, None)
    BMD = ("board", "Board Mfg Date", SHOW_XX, None)
    BM = ("board", "Board Mfg", SHOW_VALUE, "MFG Info")
    BP = ("board", "Board Product", SHOW_VALUE, "Board Name")
    BSN = ("board", "Board Serial", SHOW_XX, "Board Serial Number")
    BPN = ("board", "Board Part Number", SHOW_VALUE, None)
    BFI = ("board", "Board FRU ID", SHOW_VALUE, "FRU Version")
    BCD1 = ("board", "Board Custom Data 1", SHOW_VALUE, "FB Board PN")
    BCD2 = ("board", "Board Custom Data 2", SHOW_XX, "PCB Vendor")
    BCD3 = ("board", "Board Custom Data 3", SHOW_XX, "Batch ID")
    BCD4 = ("board", "Board Custom Data 4", SHOW_VALUE, None)
    BCD5 = ("board", "Board Custom Data 5", SHOW_XX, None)
    BCD6 = ("board", "Board Custom Data 6", SHOW_XX, None)
    PM = ("product", "Product Manufacturer", SHOW_VALUE, "MFG Info")
    PN = ("product", "Product Name", SHOW_VALUE, None)
    PPN = ("product", "Product Part Number", SHOW_VALUE, None)
    PV = ("product", "Product Version", SHOW_VALUE, None)
    PSN = ("product", "Product Serial", SHOW_XX, "Product Serial Number")
    PAT = ("product", "Product Asset Tag", SHOW_XX, None)
    PFI = ("product", "Product FRU ID", SHOW_VALUE, None)
    PCD1 = ("product", "Product Custom Data 1", SHOW_XX, None)
    PCD2 = ("product", "Product Custom Data 2", SHOW_XX, None)
    PCD3 = ("product", "Product Custom Data 3", SHOW_XX, None)
    PCD4 = ("product", "Product Custom Data 4", SHOW_XX, None)
    PCD5 = ("product", "Product Custom Data 5", SHOW_XX, None)
    PCD6 = ("product", "Product Custom Data 6", SHOW_XX, None)

    @property
    def field_name(self):
        return self.value[1]

    @property
    def display_type(self):
        return self.value[2]

    @property
    def description(self):
        return self.value[3] if self.value[3] else self.value[1]

    @classmethod
    def find_field(cls, area: str, name: str):
        for fm in cls:
            if fm.value[0] == area and fm.value[1] == name:
                return fm
        return None


@dataclass
class FRU:
    EPOCH: datetime = field(default=datetime(1996, 1, 1), init=False)
    common_header: list = field(default_factory=list)
    chassis_info: Dict[str, Any] = field(default_factory=dict)
    board_info: Dict[str, Any] = field(default_factory=dict)
    product_info: Dict[str, Any] = field(default_factory=dict)
    raw_data: bytearray = field(default_factory=bytearray)
    detail_data: List[List[str]] = field(default_factory=list)

    FIELD_ORDER = {
        "chassis": ["Chassis Part Number", "Chassis Serial Number"],
        "board": [
            "Board Mfg",
            "Board Product",
            "Board Serial",
            "Board Part Number",
            "Board FRU ID",
        ],
        "product": [
            "Product Manufacturer",
            "Product Name",
            "Product Part Number",
            "Product Version",
            "Product Serial",
            "Product Asset Tag",
            "Product FRU ID",
        ],
    }

    def parse_bin(self, filename: Path, detailed: bool = False) -> None:
        if filename is not None:
            with filename.open("rb") as f:
                self.raw_data = bytearray(f.read())
        elif not self.raw_data:
            raise ValueError("No raw data available and no filename provided")

        self.common_header = list(struct.unpack("BBBBBBBB", self.raw_data[:8]))
        if detailed:
            self.detail_data = [["Offset", "Value", "Description"]]
            fields = [
                "Common Header Format Version",
                "Internal Use Area Offset",
                "Chassis Info Area Offset",
                "Board Info Area Offset",
                "Product Info Area Offset",
                "MultiRecord Area Offset",
                "Pad",
                "Common Header Checksum",
            ]
            for i, field in enumerate(fields):
                self.append_detail_row(i, self.common_header[i], field)

            self.detail_data.append(["", "", ""])

        for area, offset in [("chassis", 2), ("board", 3), ("product", 4)]:
            if self.common_header[offset]:
                self.parse_area(area, self.common_header[offset] * 8, detailed)

    def parse_area(self, area_name: str, area_offset: int, detailed: bool) -> None:
        if area_offset + 2 > len(self.raw_data):
            return

        area_len = self.raw_data[area_offset + 1] * 8
        if area_len < 8 or area_offset + area_len > len(self.raw_data):
            return

        data = self.raw_data[area_offset : area_offset + area_len]
        if detailed:
            area_title = f"{area_name.capitalize()} Info Area"
            self.append_detail_row(area_offset, data[0], f"{area_title} Format Version")
            self.append_detail_row(area_offset + 1, data[1], f"{area_title} Length")

        info = {}
        offset = 2  # Skip format version and area length

        if area_name == "chassis":
            info["Chassis Type"] = data[offset]
            if detailed:
                self.append_detail_row(
                    area_offset + offset, data[offset], "Chassis Type"
                )
            offset += 1
        elif area_name in ["board", "product"]:
            info["Language"] = data[offset]
            if detailed:
                self.append_detail_row(
                    area_offset + offset, data[offset], "Language Code"
                )
            offset += 1
            if area_name == "board":
                info["Board Mfg Date"] = self.parse_mfg_date(data[offset : offset + 3])
                if detailed:
                    self.append_detail_row(
                        area_offset + offset,
                        data[offset : offset + 3],
                        "MFG Date Time",
                        SHOW_XX,
                    )
                offset += 3

        sum_offset = area_len - 1  # -1 to account for checksum
        while offset < sum_offset:
            type_length = data[offset]
            if type_length == 0xC1:  # End of area
                break

            length = type_length & 0x3F
            field_value = data[offset + 1 : offset + 1 + length]
            field_name = self.get_field_name(
                area_name, len(info) - (2 if area_name == "board" else 1)
            )

            info[field_name] = self.decode_field(field_value)
            if detailed:
                self.append_detail_row(
                    area_offset + offset, type_length, f"{field_name} Type/Length"
                )
                if length > 0:
                    field_enum = FieldMapping.find_field(area_name, field_name)
                    self.append_detail_row(
                        area_offset + offset + 1,
                        field_value,
                        field_enum.description,
                        field_enum.display_type,
                    )

            offset += 1 + length

        if detailed and offset < sum_offset:
            if data[offset] == 0xC1:
                self.append_detail_row(
                    area_offset + offset, data[offset], "End of Field Marker"
                )
                offset += 1

                pad_len = sum_offset - offset
                if pad_len > 0:
                    self.append_detail_row(
                        area_offset + offset,
                        data[offset : offset + pad_len],
                        "Pad",
                    )
                    offset += pad_len

        # Checksum
        calculated_checksum = self.calculate_checksum(data[:sum_offset])
        stored_checksum = data[sum_offset]
        if calculated_checksum != stored_checksum:
            logger.warning(
                f"{area_name.capitalize()} area checksum mismatch: "
                f"calculated {calculated_checksum}, stored {stored_checksum}"
            )
        if detailed:
            self.append_detail_row(
                area_offset + sum_offset,
                data[sum_offset],
                f"{area_name.capitalize()} Info Area Checksum",
                0 if area_name == "chassis" else SHOW_XX,
            )
            self.detail_data.append(["", "", ""])

        setattr(self, f"{area_name}_info", info)

    def append_detail_row(
        self, offset: int, data: Union[int, bytes, bytearray], desc: str, show: int = 0
    ) -> None:
        if isinstance(data, (bytes, bytearray)):
            length = len(data)
            if length == 1:
                offset_str = f"{offset:02X}h"
            else:
                offset_str = f"{offset:02X}h:{offset+length-1:02X}h"

            if show == SHOW_XX:
                value_str = " ".join(["XXh"] * length)
            else:
                value_str = " ".join([f"{b:02X}h" for b in data])

            if show == SHOW_VALUE:
                desc_value = "".join(
                    chr(b) if 32 <= b < 127 else "?" for b in data if b
                )
                if desc_value:
                    desc = f"{desc}: [{desc_value}]"
        else:
            offset_str = f"{offset:02X}h"
            value_str = "XXh" if show == SHOW_XX else f"{data:02X}h"

        self.detail_data.append([offset_str, value_str, desc])

    @staticmethod
    def decode_field(data: bytes) -> str:
        return data.decode("ascii").rstrip("\0")

    @classmethod
    def parse_mfg_date(cls, date_bytes: bytes) -> Dict[str, Any]:
        minutes = struct.unpack("<I", date_bytes + b"\x00")[0]
        return {"minutes": minutes, "date": cls.minutes_to_date_string(minutes)}

    @classmethod
    def minutes_to_date_string(cls, minutes: int) -> str:
        return (cls.EPOCH + timedelta(minutes=minutes)).strftime("%Y-%m-%d %H:%M:%S")

    def get_field_name(self, area_name: str, index: int) -> str:
        if index < len(self.FIELD_ORDER[area_name]):
            return self.FIELD_ORDER[area_name][index]
        return f"{area_name.capitalize()} Custom Data {index - len(self.FIELD_ORDER[area_name]) + 1}"

    def modify_field(self, field: str, value: str) -> None:
        area, full_field = FieldMapping[field].value[:2]
        info = getattr(self, f"{area}_info")
        if field == "BMD":
            date = datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
            minutes = int((date - self.EPOCH).total_seconds() / 60)
            info["Board Mfg Date"] = {"minutes": minutes, "date": value}
        else:
            info[full_field] = value

    @staticmethod
    def calculate_checksum(data: bytearray) -> int:
        return (0x100 - sum(data)) & 0xFF

    def write_bin(self, filename: Path) -> None:
        with filename.open("wb") as f:
            f.write(self.raw_data)

    def build_area(self, area_name: str) -> bytearray:
        info = getattr(self, f"{area_name}_info")
        area_data = bytearray([0x01, 0])  # Format version and initial length

        # Add area-specific headers
        if area_name == "chassis":
            chassis_type = info.get("Chassis Type", 0x17)
            if chassis_type == 0x00:
                chassis_type = 0x17
            area_data.append(chassis_type)
        elif area_name in ["board", "product"]:
            area_data.append(info.get("Language", 0x19))
            if area_name == "board":
                mfg_date = info.get("Board Mfg Date", {"minutes": 0})
                area_data.extend(struct.pack("<I", mfg_date["minutes"])[:3])

        # Find the highest used custom field
        max_custom_field = max(
            (
                int(k.split()[-1])
                for k in info.keys()
                if k.startswith(f"{area_name.capitalize()} Custom Data ")
            ),
            default=0,
        )

        # Add all fields including custom data up to max_custom_field
        fields = self.FIELD_ORDER[area_name] + [
            f"{area_name.capitalize()} Custom Data {i}"
            for i in range(1, max_custom_field + 1)
        ]

        for field in fields:
            if field in info and info[field]:
                value = info[field]
                encoded_value = (
                    value.encode("ascii") if isinstance(value, str) else bytes(value)
                )
                if len(encoded_value) == 1:
                    raise ValueError(
                        f"Field '{field}' must have a length of at least 2 characters."
                    )

                if len(encoded_value) > 63:
                    logger.warning(
                        f"Field '{field}' is too long and will be truncated."
                    )
                    encoded_value = encoded_value[:63]
                area_data.extend([0xC0 | len(encoded_value)])
                area_data.extend(encoded_value)
            else:
                area_data.extend([0x00])  # Empty or non-existent field

        # Finalize area
        area_data.extend([0xC1])  # End of area marker
        area_data.extend([0] * (-(len(area_data) + 1) % 8))  # Pad to 8-byte boundary
        area_data[1] = (len(area_data) + 1) // 8  # Update area length
        area_data.append(self.calculate_checksum(area_data))

        return area_data

    def rebuild_fru_binary(self) -> bool:
        new_data = bytearray(8)  # Space for common header

        for i, area in enumerate(["chassis", "board", "product"]):
            if getattr(self, f"{area}_info"):
                try:
                    area_data = self.build_area(area)
                except ValueError as e:
                    logger.error(f"Error building {area} area: {e}")
                    return False
                self.common_header[i + 2] = len(new_data) // 8
                new_data.extend(area_data)

        struct.pack_into("BBBBBBBB", new_data, 0, *self.common_header)
        new_data[7] = self.calculate_checksum(new_data[:7])
        self.raw_data = new_data
        return True

    def export_excel(self, filename: Path) -> None:
        try:
            import xlsxwriter
        except ImportError:
            logger.error("xlsxwriter module is not installed.")
            sys.exit(1)

        self.parse_bin(None, detailed=True)

        # Create a new workbook and select the active worksheet
        workbook = xlsxwriter.Workbook(str(filename))
        worksheet = workbook.add_worksheet("FRU Data")

        header_format = workbook.add_format(
            {
                "font_name": "Arial",
                "font_size": 12,
                "bold": True,
                "border": 1,
                "align": "center",
                "valign": "vcenter",
                "text_wrap": True,
            }
        )
        cell_format = workbook.add_format(
            {
                "font_name": "Consolas",
                "font_size": 12,
                "border": 1,
                "valign": "vcenter",
                "text_wrap": True,
            }
        )

        # Set column widths
        worksheet.set_column("A:A", 15)  # Offset column
        worksheet.set_column("B:B", 40)  # Value column
        worksheet.set_column("C:C", 50)  # Description column
        CHARS_PER_LINE = 32

        # Write data to worksheet
        for row_idx, row_data in enumerate(self.detail_data):
            # Apply row height based on content of value column
            if row_idx > 0 and len(row_data) > 1 and row_data[1]:
                line_count = (len(row_data[1]) + CHARS_PER_LINE - 1) // CHARS_PER_LINE
                if line_count > 1:
                    worksheet.set_row(row_idx, 15 * line_count)

            for col_idx, cell_value in enumerate(row_data):
                if row_idx == 0:  # Header row
                    worksheet.write(row_idx, col_idx, cell_value, header_format)
                else:
                    worksheet.write(row_idx, col_idx, cell_value, cell_format)

        workbook.close()


class FRUEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, dict) and "minutes" in obj and "date" in obj:
            return obj["date"]
        return super().default(obj)


def main():
    parser = argparse.ArgumentParser(
        description="FRU Data Parser, Modifier, and Formatter",
        usage="python3 %(prog)s fru_file [-h] [-v] [-m] [-f OUTPUT_FILE] [field options]",
    )

    parser.add_argument("fru_file", type=Path, help="path to the FRU file")
    parser.add_argument(
        "-v", "--version", action="version", version=f"fruid-util {__version__}"
    )
    parser.add_argument("-m", "--modify", action="store_true", help="modify fields")
    parser.add_argument(
        "-f",
        "--format",
        type=Path,
        metavar="",
        help="output in Excel xlsx format to specified file",
    )

    field_opt = parser.add_argument_group("field options")
    for field in FieldMapping:
        field_opt.add_argument(f"--{field.name}", help=f"modify {field.value[1]}")

    args = parser.parse_args()

    fru = FRU()
    if args.modify and not args.fru_file.exists():
        print(f"FRU file {args.fru_file} does not exist. Creating a new file.")
        fru.common_header = [0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
    else:
        fru.parse_bin(args.fru_file)

    if args.modify:
        modified = False
        for field in FieldMapping:
            value = getattr(args, field.name)
            if value is not None:
                fru.modify_field(field.name, value)
                modified = True

        if modified:
            if not args.fru_file.exists() and fru.board_info:
                if "Board Mfg Date" not in fru.board_info:
                    date_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    fru.modify_field("BMD", date_now)

            if not fru.rebuild_fru_binary():
                print("Failed to rebuild FRU binary due to errors.")
                return 1

            fru.write_bin(args.fru_file)
            print(f"FRU data has been updated and written to {args.fru_file}.")
        else:
            logger.warning("No modifications specified.")

    if args.format:
        fru.export_excel(args.format)
        print(f"Excel data written to {args.format}")

    if args.format or args.modify:
        return 0

    print(
        json.dumps(
            {
                "Chassis Info": fru.chassis_info,
                "Board Info": {
                    k: v["date"] if isinstance(v, dict) and "date" in v else v
                    for k, v in fru.board_info.items()
                },
                "Product Info": fru.product_info,
            },
            indent=2,
            cls=FRUEncoder,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
