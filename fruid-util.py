import struct
from datetime import datetime, timedelta
import argparse
import json
from typing import Dict, Any
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import logging
import sys

__version__ = "v2025.02.0"

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

CustomerDataMax = 26
base_fields = {}
base_fields["CPN"] = ("chassis", "Chassis Part Number")
base_fields["CSN"] = ("chassis", "Chassis Serial Number")
base_fields.update({f"CCD{i}": ("chassis", f"Chassis Custom Data {i}") for i in range(1, CustomerDataMax+1)})
base_fields["BMD"] = ("board", "Board Mfg Date")
base_fields["BM"] = ("board", "Board Mfg")
base_fields["BP"] = ("board", "Board Product")
base_fields["BSN"] = ("board", "Board Serial")
base_fields["BPN"] = ("board", "Board Part Number")
base_fields["BFI"] = ("board", "Board FRU ID")
base_fields.update({f"BCD{i}": ("board", f"Board Custom Data {i}") for i in range(1, CustomerDataMax+1)})
base_fields["PM"] = ("product", "Product Manufacturer")
base_fields["PN"] = ("product", "Product Name")
base_fields["PPN"] = ("product", "Product Part Number")
base_fields["PV"] = ("product", "Product Version")
base_fields["PSN"] = ("product", "Product Serial")
base_fields["PAT"] = ("product", "Product Asset Tag")
base_fields["PFI"] = ("product", "Product FRU ID")
base_fields.update({f"PCD{i}": ("product", f"Product Custom Data {i}") for i in range(1, CustomerDataMax+1)})
FieldMapping = Enum("FieldMapping", base_fields)

@dataclass
class FRU:
    EPOCH: datetime = field(default=datetime(1996, 1, 1), init=False)
    common_header: list = field(default_factory=list)
    chassis_info: Dict[str, Any] = field(default_factory=dict)
    board_info: Dict[str, Any] = field(default_factory=dict)
    product_info: Dict[str, Any] = field(default_factory=dict)
    raw_data: bytearray = field(default_factory=bytearray)

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

    def parse_bin(self, filename: Path) -> None:
        with filename.open("rb") as f:
            self.raw_data = bytearray(f.read())

        self.common_header = list(struct.unpack("BBBBBB", self.raw_data[:6]))

        for area, offset in [("chassis", 2), ("board", 3), ("product", 4)]:
            if self.common_header[offset]:
                self.parse_area(self.raw_data[self.common_header[offset] * 8 :], area)

    def parse_area(self, data: bytearray, area_name: str) -> None:
        info = {}
        offset = 2  # Skip format version and area length
        area_length = data[1] * 8

        if area_name == "chassis":
            info["Chassis Type"] = data[offset]
            offset += 1
        elif area_name in ["board", "product"]:
            info["Language"] = data[offset]
            offset += 1
            if area_name == "board":
                info["Board Mfg Date"] = self.parse_mfg_date(data[offset : offset + 3])
                offset += 3

        while offset < area_length - 1:  # -1 to account for checksum
            type_length = data[offset]
            if type_length == 0xC1:  # End of area
                break

            offset += 1
            length = type_length & 0x3F
            value = self.decode_field(data[offset : offset + length])
            field_name = self.get_field_name(
                area_name, len(info) - (2 if area_name == "board" else 1)
            )
            info[field_name] = value
            offset += length

        # Verify checksum
        calculated_checksum = self.calculate_checksum(data[: area_length - 1])
        stored_checksum = data[area_length - 1]
        if calculated_checksum != stored_checksum:
            logger.warning(
                f"{area_name.capitalize()} area checksum mismatch: "
                f"calculated {calculated_checksum}, stored {stored_checksum}"
            )

        setattr(self, f"{area_name}_info", info)

    @staticmethod
    def decode_field(data: bytes) -> str:
        return data.decode("ascii").rstrip("\x00")

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
        area, full_field = FieldMapping[field].value
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
            area_data.append(info.get("Chassis Type", 0x17))
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

        struct.pack_into("BBBBBB", new_data, 0, *self.common_header)
        new_data[7] = self.calculate_checksum(new_data[:7])
        self.raw_data = new_data
        return True


class FRUEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, dict) and "minutes" in obj and "date" in obj:
            return obj["date"]
        return super().default(obj)


def main():
    parser = argparse.ArgumentParser(
        description="FRU Data Parser and Modifier",
        usage="python3 %(prog)s fru_file [-h] [-v] [-m] [field options]",
    )

    parser.add_argument("fru_file", type=Path, help="path to the FRU file")
    parser.add_argument(
        "-v", "--version", action="version", version=f"fruid-util {__version__}"
    )
    parser.add_argument("-m", "--modify", action="store_true", help="modify fields")

    field_opt = parser.add_argument_group("field options")
    for field in FieldMapping:
        field_opt.add_argument(f"--{field.name}", help=f"modify {field.value[1]}")

    args = parser.parse_args()

    fru = FRU()
    if args.modify and not args.fru_file.exists():
        print(f"FRU file {args.fru_file} does not exist. Creating a new file.")
        fru.common_header = [0x01, 0x00, 0x00, 0x00, 0x00, 0x00]
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
            return 0
        else:
            logger.warning("No modifications specified.")
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