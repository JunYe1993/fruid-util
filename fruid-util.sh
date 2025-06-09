#!/bin/bash

VERSION="v2025.16.0"

declare -A chassis_info
declare -A board_info
declare -A product_info
declare -A FIELD_ORDER_CHASSIS
declare -a FIELD_ORDER_CHASSIS_KEYS
declare -A FIELD_ORDER_BOARD
declare -a FIELD_ORDER_BOARD_KEYS
declare -A FIELD_ORDER_PRODUCT
declare -a FIELD_ORDER_PRODUCT_KEYS

# Chassis fields
FIELD_ORDER_CHASSIS[CPN]="Part Number"; FIELD_ORDER_CHASSIS_KEYS+=("CPN")
FIELD_ORDER_CHASSIS[CSN]="Serial Number"; FIELD_ORDER_CHASSIS_KEYS+=("CSN")
FIELD_ORDER_CHASSIS[CCD1]="Custom Data 1"; FIELD_ORDER_CHASSIS_KEYS+=("CCD1")
FIELD_ORDER_CHASSIS[CCD2]="Custom Data 2"; FIELD_ORDER_CHASSIS_KEYS+=("CCD2")
FIELD_ORDER_CHASSIS[CCD3]="Custom Data 3"; FIELD_ORDER_CHASSIS_KEYS+=("CCD3")
FIELD_ORDER_CHASSIS[CCD4]="Custom Data 4"; FIELD_ORDER_CHASSIS_KEYS+=("CCD4")
FIELD_ORDER_CHASSIS[CCD5]="Custom Data 5"; FIELD_ORDER_CHASSIS_KEYS+=("CCD5")
FIELD_ORDER_CHASSIS[CCD6]="Custom Data 6"; FIELD_ORDER_CHASSIS_KEYS+=("CCD6")
FIELD_ORDER_CHASSIS[CCD7]="Custom Data 7"; FIELD_ORDER_CHASSIS_KEYS+=("CCD7")
FIELD_ORDER_CHASSIS[CCD8]="Custom Data 8"; FIELD_ORDER_CHASSIS_KEYS+=("CCD8")
FIELD_ORDER_CHASSIS[CCD9]="Custom Data 9"; FIELD_ORDER_CHASSIS_KEYS+=("CCD9")
FIELD_ORDER_CHASSIS[CCD10]="Custom Data 10"; FIELD_ORDER_CHASSIS_KEYS+=("CCD10")
FIELD_ORDER_CHASSIS[CCD11]="Custom Data 11"; FIELD_ORDER_CHASSIS_KEYS+=("CCD11")
FIELD_ORDER_CHASSIS[CCD12]="Custom Data 12"; FIELD_ORDER_CHASSIS_KEYS+=("CCD12")
FIELD_ORDER_CHASSIS[CCD13]="Custom Data 13"; FIELD_ORDER_CHASSIS_KEYS+=("CCD13")
FIELD_ORDER_CHASSIS[CCD14]="Custom Data 14"; FIELD_ORDER_CHASSIS_KEYS+=("CCD14")
FIELD_ORDER_CHASSIS[CCD15]="Custom Data 15"; FIELD_ORDER_CHASSIS_KEYS+=("CCD15")
FIELD_ORDER_CHASSIS[CCD16]="Custom Data 16"; FIELD_ORDER_CHASSIS_KEYS+=("CCD16")
FIELD_ORDER_CHASSIS[CCD17]="Custom Data 17"; FIELD_ORDER_CHASSIS_KEYS+=("CCD17")
FIELD_ORDER_CHASSIS[CCD18]="Custom Data 18"; FIELD_ORDER_CHASSIS_KEYS+=("CCD18")
FIELD_ORDER_CHASSIS[CCD19]="Custom Data 19"; FIELD_ORDER_CHASSIS_KEYS+=("CCD19")
FIELD_ORDER_CHASSIS[CCD20]="Custom Data 20"; FIELD_ORDER_CHASSIS_KEYS+=("CCD20")
FIELD_ORDER_CHASSIS[CCD21]="Custom Data 21"; FIELD_ORDER_CHASSIS_KEYS+=("CCD21")
FIELD_ORDER_CHASSIS[CCD22]="Custom Data 22"; FIELD_ORDER_CHASSIS_KEYS+=("CCD22")
FIELD_ORDER_CHASSIS[CCD23]="Custom Data 23"; FIELD_ORDER_CHASSIS_KEYS+=("CCD23")
FIELD_ORDER_CHASSIS[CCD24]="Custom Data 24"; FIELD_ORDER_CHASSIS_KEYS+=("CCD24")

# Board fields
FIELD_ORDER_BOARD[BMD]="Mfg Date"; FIELD_ORDER_BOARD_KEYS+=("BMD")
FIELD_ORDER_BOARD[BM]="Manufacturer"; FIELD_ORDER_BOARD_KEYS+=("BM")
FIELD_ORDER_BOARD[BP]="Product Name"; FIELD_ORDER_BOARD_KEYS+=("BP")
FIELD_ORDER_BOARD[BSN]="Serial Number"; FIELD_ORDER_BOARD_KEYS+=("BSN")
FIELD_ORDER_BOARD[BPN]="Part Number"; FIELD_ORDER_BOARD_KEYS+=("BPN")
FIELD_ORDER_BOARD[BFI]="FRU File ID"; FIELD_ORDER_BOARD_KEYS+=("BFI")
FIELD_ORDER_BOARD[BCD1]="Custom Data 1"; FIELD_ORDER_BOARD_KEYS+=("BCD1")
FIELD_ORDER_BOARD[BCD2]="Custom Data 2"; FIELD_ORDER_BOARD_KEYS+=("BCD2")
FIELD_ORDER_BOARD[BCD3]="Custom Data 3"; FIELD_ORDER_BOARD_KEYS+=("BCD3")
FIELD_ORDER_BOARD[BCD4]="Custom Data 4"; FIELD_ORDER_BOARD_KEYS+=("BCD4")
FIELD_ORDER_BOARD[BCD5]="Custom Data 5"; FIELD_ORDER_BOARD_KEYS+=("BCD5")
FIELD_ORDER_BOARD[BCD6]="Custom Data 6"; FIELD_ORDER_BOARD_KEYS+=("BCD6")

# Product fields
FIELD_ORDER_PRODUCT[PM]="Manufacturer"; FIELD_ORDER_PRODUCT_KEYS+=("PM")
FIELD_ORDER_PRODUCT[PN]="Product Name"; FIELD_ORDER_PRODUCT_KEYS+=("PN")
FIELD_ORDER_PRODUCT[PPN]="Part Number"; FIELD_ORDER_PRODUCT_KEYS+=("PPN")
FIELD_ORDER_PRODUCT[PV]="Version"; FIELD_ORDER_PRODUCT_KEYS+=("PV")
FIELD_ORDER_PRODUCT[PSN]="Serial Number"; FIELD_ORDER_PRODUCT_KEYS+=("PSN")
FIELD_ORDER_PRODUCT[PAT]="Asset Tag"; FIELD_ORDER_PRODUCT_KEYS+=("PAT")
FIELD_ORDER_PRODUCT[PFI]="FRU File ID"; FIELD_ORDER_PRODUCT_KEYS+=("PFI")
FIELD_ORDER_PRODUCT[PCD1]="Custom Data 1"; FIELD_ORDER_PRODUCT_KEYS+=("PCD1")
FIELD_ORDER_PRODUCT[PCD2]="Custom Data 2"; FIELD_ORDER_PRODUCT_KEYS+=("PCD2")
FIELD_ORDER_PRODUCT[PCD3]="Custom Data 3"; FIELD_ORDER_PRODUCT_KEYS+=("PCD3")
FIELD_ORDER_PRODUCT[PCD4]="Custom Data 4"; FIELD_ORDER_PRODUCT_KEYS+=("PCD4")
FIELD_ORDER_PRODUCT[PCD5]="Custom Data 5"; FIELD_ORDER_PRODUCT_KEYS+=("PCD5")
FIELD_ORDER_PRODUCT[PCD6]="Custom Data 6"; FIELD_ORDER_PRODUCT_KEYS+=("PCD6")

# Function to read bytes from file
read_bytes() {
    dd if="$1" bs=1 skip="$2" count="$3" 2>/dev/null | hexdump -v -e '/1 "%02x"'
}

# Function to convert hex to decimal
hex_to_dec() {
    printf "%d" "0x$1"
}

# Function to convert ASCII to hex
ascii_to_hex() {
    printf '%s' "$1" | hexdump -v -e '/1 "%02x"'
}

# Function to convert hex to ASCII
hex_to_ascii() {
    local hex="$1"
    local ascii=""
    for ((i=0; i<${#hex}; i+=2)); do
        ascii+=$(printf '%b' "\x${hex:$i:2}")
    done
    printf '%s' "$ascii"
}

# Function to convert raw bytes to date
convert_mfg_date() {
    local timestamp=$(($(date -d "1996-01-01 00:00:00" +%s) + $(printf "0x%06x" "0x${1:4:2}${1:2:2}${1:0:2}") * 60))
    date -d "@$timestamp" "+%Y-%m-%d %H:%M:%S"
}

# Function to convert date string to raw FRU format
date_to_raw_fru() {
    local minutes=$((($(date -d "$1" +%s) - $(date -d "1996-01-01 00:00:00" +%s)) / 60))
    printf "%02x%02x%02x" $((minutes & 0xFF)) $(((minutes >> 8) & 0xFF)) $(((minutes >> 16) & 0xFF))
}

# Function to calculate checksum
calculate_checksum() {
    local data="$1"
    local sum=0
    for ((i=0; i<${#data}; i+=2)); do
        sum=$((sum + 0x${data:$i:2}))
    done
    printf "%02x" $(((0x100 - (sum & 0xFF)) & 0xFF))
}

# Function to verify checksum
verify_checksum() {
    local data="$1"
    local checksum="${data: -2}"
    local calculated=""
    calculated=$(calculate_checksum "${data:0:-2}")
    if [ "$calculated" != "$checksum" ]; then
        echo "Checksum MISMATCH (Calculated: $calculated, Found: $checksum)"
        return 1
    fi
    return 0
}

# Function to parse FRU binary file
parse_fru() {
    local file="$1"
    local common_header=""
    local area=""
    local offset=0
    local area_length=0
    local area_data=""

    # Read the common header
    common_header=$(read_bytes "$file" 0 8)
    verify_checksum "$common_header" || echo "Common Header: Checksum error detected"

    # Parse areas
    for i in {0..2}; do
        case $i in
            0) area="Chassis" ;;
            1) area="Board" ;;
            2) area="Product" ;;
        esac
        offset=$(($(hex_to_dec "${common_header:$(((i+2)*2)):2}") * 8))
        [ $offset -eq 0 ] && continue

        area_length=$(($(hex_to_dec "$(read_bytes "$file" $((offset + 1)) 1)") * 8))
        area_data=$(read_bytes "$file" $offset $area_length)
        verify_checksum "$area_data" || echo "${area} Info: Checksum error detected"

        parse_area "$area_data" "$area"
    done
}

# Function to parse an area
parse_area() {
    local area_data="$1"
    local area="$2"
    local offset=4  # Skip format version and area length
    local field_index=0
    local -n area_info
    local -n area_fields
    local -n field_order_keys

    case "$area" in
        "Chassis")
            area_info=chassis_info
            area_fields=FIELD_ORDER_CHASSIS
            field_order_keys=FIELD_ORDER_CHASSIS_KEYS
            area_info["Chassis Type"]="${area_data:offset:2}"
            offset=$((offset + 2))
            ;;
        "Board")
            area_info=board_info
            area_fields=FIELD_ORDER_BOARD
            field_order_keys=FIELD_ORDER_BOARD_KEYS
            area_info["Language"]="${area_data:offset:2}"
            offset=$((offset + 2))
            area_info["Mfg Date"]="${area_data:offset:6}"
            offset=$((offset + 6))
            field_index=1  # Skip Mfg Date as it's already handled
            ;;
        "Product")
            area_info=product_info
            area_fields=FIELD_ORDER_PRODUCT
            field_order_keys=FIELD_ORDER_PRODUCT_KEYS
            area_info["Language"]="${area_data:offset:2}"
            offset=$((offset + 2))
            ;;
        *)
            echo "Unknown area: $area"
            return 1
            ;;
    esac

    while [ $offset -lt $((${#area_data} - 2)) ]; do
        local type_length="${area_data:offset:2}"
        [ "$type_length" = c1 ] && break  # End of area
        [ $field_index -ge ${#field_order_keys[@]} ] && break

        offset=$((offset + 2))
        local field_length=$((0x$type_length & 0x3f))

        # Store data in respective area's dictionary
        local field_code=${field_order_keys[$field_index]}
        local field_name=${area_fields[$field_code]}
        area_info["$field_name"]=$(hex_to_ascii "${area_data:offset:field_length*2}")

        offset=$((offset + field_length*2))
        field_index=$((field_index + 1))
    done
}

# Function to display parsed info
print_fru_info() {
    local area=""
    local field_code=""
    local field_name=""

    for area in "Chassis" "Board" "Product"; do
        local -n area_info="${area,,}_info"
        local -n area_fields="FIELD_ORDER_${area^^}"
        local -n field_order_keys="FIELD_ORDER_${area^^}_KEYS"

        # Check if the area is empty
        if [ -z "${area_info[*]}" ]; then
            echo "${area} Info: N/A"
            echo
            continue
        fi

        echo "${area} Info:"
        case "$area" in
            "Chassis")
                echo "  Chassis Type: 0x${chassis_info["Chassis Type"]}"
                ;;
            "Board")
                echo "  Language: 0x${board_info["Language"]}"
                ;;
            "Product")
                echo "  Language: 0x${product_info["Language"]}"
                ;;
        esac

        for field_code in "${field_order_keys[@]}"; do
            field_name="${area_fields[$field_code]}"
            if [ -n "${area_info[$field_name]}" ]; then
                if [[ "$field_name" == "Mfg Date" ]]; then
                    echo "  $field_name: $(convert_mfg_date "${area_info[$field_name]}")"
                else
                    echo "  $field_name: ${area_info[$field_name]}"
                fi
            fi
        done
        echo
    done
}

# Function to modify a field
modify_field() {
    local field="$1"
    local new_value="$2"
    local field_name=""
    local -n area_info
    local -n area_fields

    case "${field:0:1}" in
        C)
            area_info=chassis_info
            area_fields=FIELD_ORDER_CHASSIS
            ;;
        B)
            area_info=board_info
            area_fields=FIELD_ORDER_BOARD
            ;;
        P)
            area_info=product_info
            area_fields=FIELD_ORDER_PRODUCT
            ;;
        *)
            echo "Unknown field: $field"
            return 1
            ;;
    esac

    if [ -v "area_fields[$field]" ]; then
        field_name="${area_fields[$field]}"
        if [[ "$field" == "BMD" ]]; then
            area_info[$field_name]=$(date_to_raw_fru "$new_value")
            echo "Board Mfg Date updated to '$new_value'"
        else
            area_info[$field_name]="$new_value"
            #echo "Field '$field_name' updated to '$new_value'"
        fi
    else
        echo "Unknown field: $field"
        return 1
    fi
}

# Function to build an area
build_area() {
    local area_name="$1"
    local area_data=""
    local field_code=""
    local encoded_value=""
    local -n area_info="${area_name}_info"
    local -n area_fields="FIELD_ORDER_${area_name^^}"
    local -n field_order_keys="FIELD_ORDER_${area_name^^}_KEYS"

    # Format version and initial length
    area_data+="0100"

    # Add area-specific headers
    case "$area_name" in
        chassis)
            local chassis_type="${area_info["Chassis Type"]:-17}"
            [[ "$chassis_type" == "00" ]] && chassis_type="17"
            area_data+="$chassis_type"
            ;;
        board)
            area_data+="${area_info["Language"]:-19}"
            area_data+="${area_info["Mfg Date"]:-000000}"
            ;;
        product)
            area_data+="${area_info["Language"]:-19}"
            ;;
    esac

    # Find the highest used custom field
    local max_custom_field=0
    for i in {1..24}; do
        if [ -n "${area_info["Custom Data $i"]}" ]; then
            max_custom_field=$i
        fi
    done

    # Add all fields including custom data
    for field_code in "${field_order_keys[@]}"; do
        local field="${area_fields[$field_code]}"
        # Skip Mfg Date as it's already handled
        if [[ "$field" == "Mfg Date" ]]; then
            continue
        fi

        # Skip custom data fields beyond the highest used one
        if [[ $field == "Custom Data"* && ${field##* } -gt $max_custom_field ]]; then
            continue
        fi

        if [ -n "${area_info[$field]}" ]; then
            encoded_value=$(ascii_to_hex "${area_info[$field]}")
            local length=$((${#encoded_value} / 2))
            if [ $length -eq 1 ]; then
                echo "Error: Field '$field' must have a length of at least 2 characters." >&2
                return 1
            fi

            if [ $length -gt 63 ]; then
                echo "Warning: Field '$field' is too long and will be truncated." >&2
                encoded_value="${encoded_value:0:126}"
                length=63
            fi
            area_data+=$(printf "%02x" $((0xC0 | length)))$encoded_value
        else
            area_data+="00"  # Empty or non-existent field
        fi
    done

    # Finalize area
    area_data+="c1"  # End of area marker

    # Pad to 8-byte boundary
    local padding=$((((8 - (${#area_data} / 2 + 1) % 8) % 8) * 2))
    if [ $padding -ne 0 ]; then
        area_data+=$(printf '%0*x' $padding 0)
    fi

    # Update area length
    area_data="01$(printf "%02x" $(((${#area_data} / 2 + 1) / 8)))${area_data:4}"

    # Add checksum
    area_data+="$(calculate_checksum "$area_data")"

    echo "$area_data"
    return 0
}

# Function to rebuild FRU binary
rebuild_fru_binary() {
    local file="$1"
    local common_header="0100000000000000"
    local area=""
    local offset=8  # Start after the 8-byte common header
    local area_data=""
    local new_data=""

    for i in {2..4}; do
        case $i in
            2) area="chassis" ;;
            3) area="board" ;;
            4) area="product" ;;
        esac
        local -n area_info="${area}_info"
        [ -z "${area_info[*]}" ] && continue

        common_header="$(printf '%s%02x%s' "${common_header:0:$((i*2))}" $((offset/8)) "${common_header:$((i*2+2))}")"
        if ! area_data=$(build_area "$area"); then
            return 1
        fi
        new_data+="$area_data"
        offset=$((offset + ${#area_data} / 2))
    done

    # Calculate and add common header checksum
    common_header="${common_header:0:14}$(calculate_checksum "${common_header:0:14}")"

    # Combine common header and area data
    new_data="${common_header}${new_data}"

    # Write the new data to the file
    printf '%b' "$(echo -n "$new_data" | sed 's/\(..\)/\\x\1/g')" > "$file"
    echo "Binary file rebuilt successfully"
    return 0
}

show_help() {
    cat << EOF
Usage: $0 [-h] [-m] [-v] [OPTIONS] fru_file

options:
  -h, --help      show this help message and exit
  -m, --modify    modify fields
  -v, --version   show program's version number and exit

EOF
    for area in Chassis Board Product; do
        local -n keys="FIELD_ORDER_${area^^}_KEYS"
        local -n fields="FIELD_ORDER_${area^^}"
        echo "  ${area} options:"
        for key in "${keys[@]}"; do
            printf "    --%-4s %-5s  %s %s\n" "$key" "$key" "modify" "${fields[$key]}"
        done
        echo
    done
}

# Main script
fru_file=""
modify_mode=false
create_file=false
declare -a modify_options

# Parse arguments
while [ $# -gt 0 ]; do
    case "$1" in
        -h|--help)
            show_help
            exit 0
            ;;
        -v|--version)
            echo "fruid-util $VERSION"
            exit 0
            ;;
        -m|--modify)
            modify_mode=true
            ;;
        --*)
            if [ "$modify_mode" = true ]; then
                modify_options+=("$1" "$2")
                shift
            else
                echo "Unknown option: $1"
                exit 1
            fi
            ;;
        *)
            if [ -z "$fru_file" ]; then
                fru_file="$1"
            else
                echo "Error: Multiple FRU files specified"
                exit 1
            fi
            ;;
    esac
    shift
done

if [ -z "$fru_file" ]; then
    echo "Error: No FRU file specified"
    show_help
    exit 1
fi

if [ ! -f "$fru_file" ]; then
    if [ "$modify_mode" = true ]; then
        echo "FRU file $fru_file does not exist. Creating a new file."
        create_file=true
    else
        echo "Error: FRU file not found: $fru_file"
        exit 1
    fi
else
    parse_fru "$fru_file"
fi

if [ "$modify_mode" = true ]; then
    modified=false
    for ((i=0; i<${#modify_options[@]}; i+=2)); do
        option="${modify_options[i]}"
        value="${modify_options[i+1]}"
        valid_option=false
        for area in CHASSIS BOARD PRODUCT; do
            eval "keys=(\${FIELD_ORDER_${area}_KEYS[@]})"
            for key in "${keys[@]}"; do
                if [ "--$key" = "$option" ]; then
                    modify_field "$key" "$value"
                    modified=true
                    valid_option=true
                    break 2
                fi
            done
        done
        if [ "$valid_option" = false ]; then
            echo "Unknown option: $option"
            exit 1
        fi
    done

    if [ "$modified" = true ]; then
        if [[ $create_file == true && -n "${board_info[*]}" ]]; then
            board_info["Mfg Date"]=$(date_to_raw_fru "$(date '+%Y-%m-%d %H:%M:%S')")
        fi
        if ! rebuild_fru_binary "$fru_file"; then
            echo "Failed to rebuild FRU binary due to errors."
            exit 1
        fi
        echo "FRU data has been updated and written to ${fru_file}."
        exit 0
    else
        echo "No modifications specified."
        exit 1
    fi
fi

print_fru_info

