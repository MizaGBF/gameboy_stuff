import traceback

# DOC
# https://gbdev.gg8.se/wiki/articles/The_Cartridge_Header

L_HEADP = (0x134, 0x14C)
L_ENTRY = (0x100, 0x103)
L_NLOGO = (0x104, 0x133)
L_TITLE = (0x134, 0x143)
L_MANUF = (0x13F, 0x142)
L_GBCFL = (0x143, 0x143)
L_LICEN = (0x144, 0x145)
L_SGBFL = (0x146, 0x146)
L_CARDT = (0x147, 0x147)
L_ROMSZ = (0x148, 0x148)
L_RAMSZ = (0x149, 0x149)
L_DESTC = (0x14A, 0x14A)
L_LICEO = (0x14B, 0x14B)
L_MVNUM = (0x14C, 0x14C)
L_HCHCK = (0x14D, 0x14D)
L_GCHCK = (0x14E, 0x14F)
KILOBYTE = 1024
MEGABYTE = KILOBYTE*KILOBYTE

def get_section(rom : bytes, location : tuple) -> bytes:
    return rom[location[0]:location[1]+1]

def hex2int(h : str) -> int:
    return int(h, 16)

def checkHeaderChecksum(rom : bytes) -> bool:
    header = get_section(rom, L_HEADP)
    sum = 0
    for b in header:
        sum = (sum - b - 1) % 0x100
    return sum == get_section(rom, L_HCHCK)[0]

def checkLogo(rom : bytes) -> bool:
    logo = [
       0xCE, 0xED, 0x66, 0x66, 0xCC, 0x0D, 0x00, 0x0B, 0x03, 0x73, 0x00, 0x83, 0x00, 0x0C, 0x00, 0x0D,
       0x00, 0x08, 0x11, 0x1F, 0x88, 0x89, 0x00, 0x0E, 0xDC, 0xCC, 0x6E, 0xE6, 0xDD, 0xDD, 0xD9, 0x99,
       0xBB, 0xBB, 0x67, 0x63, 0x6E, 0x0E, 0xEC, 0xCC, 0xDD, 0xDC, 0x99, 0x9F, 0xBB, 0xB9, 0x33, 0x3E
    ]
    for i, b in enumerate(get_section(rom, L_NLOGO)):
        if b != logo[i]:
            return False
    return True

def title(rom : bytes) -> str:
    title = get_section(rom, L_TITLE)
    for i, b in enumerate(title):
        if b == 0x00:
            return title[:i].decode('utf-8')
    return title.decode('utf-8')

def version(rom : bytes) -> int:
    return get_section(rom, L_MVNUM)[0]

def isSGB(rom : bytes) -> bool:
    return get_section(rom, L_SGBFL)[0] == 0x03

def isCGB(rom : bytes) -> bool:
    return get_section(rom, L_GBCFL)[0] == 0x80

def isJP(rom : bytes) -> bool:
    return get_section(rom, L_DESTC)[0] == 0x00

def cardType(rom : bytes) -> str:
    return {
        0x00: "ROM ONLY",
        0x01: "MBC1",
        0x02: "MBC1+RAM",
        0x03: "MBC1+RAM+BATTERY",
        0x05: "MBC2",
        0x06: "MBC2+BATTERY",
        0x08: "ROM+RAM",
        0x09: "ROM+RAM+BATTERY",
        0x0B: "MMM01",
        0x0C: "MMM01+RAM",
        0x0D: "MMM01+RAM+BATTERY",
        0x0F: "MBC3+TIMER+BATTERY",
        0x10: "MBC3+TIMER+RAM+BATTERY",
        0x11: "MBC3",
        0x12: "MBC3+RAM",
        0x13: "MBC3+RAM+BATTERY",
        0x19: "MBC5",
        0x1A: "MBC5+RAM",
        0x1B: "MBC5+RAM+BATTERY",
        0x1C: "MBC5+RUMBLE",
        0x1D: "MBC5+RUMBLE+RAM",
        0x1E: "MBC5+RUMBLE+RAM+BATTERY",
        0x20: "MBC6",
        0x22: "MBC7+SENSOR+RUMBLE+RAM+BATTERY",
        0xFC: "POCKET CAMERA",
        0xFD: "BANDAI TAMA5",
        0xFE: "HuC3",
        0xFF: "HuC1+RAM+BATTERY"
    }.get(get_section(rom, L_CARDT)[0], "UNKNOWN")

def romSizeBank(rom : bytes) -> int:
    is_mbc1 = "MBC1" in cardType(rom)
    return {
        0x00: 0, # 32k
        0x01: 4, # 64k
        0x02: 8,
        0x03: 16,
        0x04: 32,
        0x05: (63 if is_mbc1 else 64),
        0x06: (125 if is_mbc1 else 128),
        0x52: 72,
        0x53: 80,
        0x54: 96
    }.get(get_section(rom, L_ROMSZ)[0], -1)

def extRamSize(rom : bytes) -> int:
    if "MBC2" in cardType(rom):
        return 512*4
    else:
        return {
            0x00: 0,
            0x01: 2,
            0x02: 8,
            0x03: 32,
            0x04: 128,
            0x05: 64
        }.get(get_section(rom, L_RAMSZ)[0], -1) * KILOBYTE

def load_rom(path : str) -> dict:
    ext_check = path.split('.')[-1]
    if ext_check not in ["gb"]:
        print("Extension for this file is unknown or unsupported")
        return False
    try:
        with open(path, mode="rb") as f:
            header = f.read(0x150)
        data = {
            "title": title(header),
            "valid_file": checkHeaderChecksum(header) and checkLogo(header),
            "version": version(header),
            "japan": isJP(header),
            "super": isSGB(header),
            "color": isCGB(header),
            "card_type": cardType(header),
            "rom_bank": romSizeBank(header),
            "external_ram": extRamSize(header)
        }
        return data
    except Exception as e:
        print("".join(traceback.format_exception(type(e), e, e.__traceback__)))
        print("The above exception occured")
        return {"valid_file":False}

if __name__ == "__main__":
    print(load_rom("Donkey Kong.gb"))