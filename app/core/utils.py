import re

def normalize_and_validate_mac(mac: str) -> str:
    """
    Siivoaa, normalisoi ja validoi MAC-osoitteen.
    Heittää ValueErrorin, jos muoto on väärä.
    """
    if not mac:
        raise ValueError("MAC address cannot be empty")

    # 1. Siivous ja normalisointi
    v = mac.strip().upper().replace("-", ":")
    
    # 2. Validointi regexillä (XX:XX:XX:XX:XX:XX)
    regex = r"^([0-9A-F]{2}:){5}[0-9A-F]{2}$"
    if not re.match(regex, v):
        raise ValueError("Invalid MAC address format. Use XX:XX:XX:XX:XX:XX")
        
    return v