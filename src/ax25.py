AX25_FLAG = 0x7E
AX25_UI_CONTROL = 0x03
AX25_NO_LAYER3_PID = 0xF0


def parse_address(address: str):
    """
    Convert an address such as:
        ORBITL-1

    into:
        callsign = ORBITL
        ssid = 1
    """

    address = address.upper()

    if "-" in address:
        callsign, ssid_text = address.rsplit("-", 1)
        ssid = int(ssid_text)
    else:
        callsign = address
        ssid = 0

    if len(callsign) > 6:
        raise ValueError("AX.25 callsign must be 6 characters or fewer")

    if not 0 <= ssid <= 15:
        raise ValueError("AX.25 SSID must be between 0 and 15")

    return callsign, ssid


def encode_address(address: str, last: bool) -> bytes:
    """
    Encode one AX.25 address field.

    Each address contains:
        6 callsign bytes
        1 SSID byte
    """

    callsign, ssid = parse_address(address)

    # AX.25 callsigns are always 6 characters.
    # Short callsigns are padded with spaces.
    callsign = callsign.ljust(6)

    result = bytearray()

    for character in callsign:
        ascii_value = ord(character)

        # AX.25 stores callsign characters shifted left by one bit.
        encoded_value = ascii_value << 1

        result.append(encoded_value)

    # Reserved bits are set according to the prototype baseline.
    ssid_byte = 0x60 | (ssid << 1)

    # Lowest bit indicates whether this is the final address field.
    if last:
        ssid_byte |= 0x01

    result.append(ssid_byte)

    return bytes(result)

def decode_address(data: bytes):
    """
    Decode one AX.25 address field.

    Example:
        9E A4 84 92 A8 98 63

    becomes:
        callsign = ORBITL
        ssid = 1
    """

    if len(data) != 7:
        raise ValueError("AX.25 address must contain exactly 7 bytes")

    callsign = ""

    for byte in data[:6]:
        ascii_value = byte >> 1
        callsign += chr(ascii_value)

    callsign = callsign.strip()

    ssid = (data[6] >> 1) & 0x0F

    # Bit 0 indicates whether this is the final address field.
    last = bool(data[6] & 0x01)

    return callsign, ssid, last


def crc16_x25(data: bytes) -> int:
    """
    Calculate CRC-16/X-25 used for the AX.25 FCS.
    """

    crc = 0xFFFF

    for byte in data:
        crc ^= byte

        for _ in range(8):
            if crc & 0x0001:
                crc = (crc >> 1) ^ 0x8408
            else:
                crc >>= 1

    return crc ^ 0xFFFF


def build_ui_frame(
    destination: str,
    source: str,
    information: bytes
) -> bytes:
    """
    Build the prototype AX.25 UI frame.
    """

    frame_body = bytearray()

    # Destination is not the last address.
    frame_body.extend(
        encode_address(destination, last=False)
    )

    # Source is currently the last address because
    # this prototype does not use digipeaters.
    frame_body.extend(
        encode_address(source, last=True)
    )

    frame_body.append(AX25_UI_CONTROL)
    frame_body.append(AX25_NO_LAYER3_PID)

    frame_body.extend(information)

    # Calculate FCS over address + control + PID + information.
    fcs = crc16_x25(frame_body)

    # AX.25 places the low FCS byte first.
    frame_body.append(fcs & 0xFF)
    frame_body.append((fcs >> 8) & 0xFF)

    # For now these flags are a logical representation.
    return (
        bytes([AX25_FLAG])
        + bytes(frame_body)
        + bytes([AX25_FLAG])
    )

def decode_ui_frame(frame: bytes):
    """
    Decode the prototype AX.25 UI frame.
    """

    # Minimum frame:
    # Flag + Destination + Source + Control + PID + FCS + Flag
    if len(frame) < 20:
        raise ValueError("AX.25 frame is too short")

    if frame[0] != AX25_FLAG:
        raise ValueError("Missing opening AX.25 flag")

    if frame[-1] != AX25_FLAG:
        raise ValueError("Missing closing AX.25 flag")

    # Remove opening and closing flags.
    raw_frame = frame[1:-1]

    # AX.25 stores the low FCS byte first.
    received_fcs = (
        raw_frame[-2]
        | (raw_frame[-1] << 8)
    )

    # Remove FCS before recalculating CRC.
    frame_body = raw_frame[:-2]

    calculated_fcs = crc16_x25(frame_body)

    if received_fcs != calculated_fcs:
        raise ValueError("AX.25 FCS/CRC validation failed")

    # Decode destination address.
    destination = decode_address(
        frame_body[0:7]
    )

    # Decode source address.
    source = decode_address(
        frame_body[7:14]
    )

    control = frame_body[14]

    pid = frame_body[15]

    information = frame_body[16:]

    return {
        "destination": {
            "callsign": destination[0],
            "ssid": destination[1],
            "last": destination[2],
        },
        "source": {
            "callsign": source[0],
            "ssid": source[1],
            "last": source[2],
        },
        "control": control,
        "pid": pid,
        "information": information,
        "received_fcs": received_fcs,
        "calculated_fcs": calculated_fcs,
    }