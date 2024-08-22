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
HEADER_END = L_GCHCK[1]+1
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

def check_rom(path : str) -> dict:
    ext_check = path.split('.')[-1]
    if ext_check not in ["gb"]:
        print("Extension for this file is unknown or unsupported")
        return False
    try:
        with open(path, mode="rb") as f:
            header = f.read(HEADER_END)
        data = {
            "path" : path,
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


def test_read_opcodes(rom_headers : dict) -> dict:
    try:
        with open(rom_headers["path"], mode="rb") as f:
            rom = f.read()
        read_code(rom, L_ENTRY[0])
    except Exception as e:
        print("".join(traceback.format_exception(type(e), e, e.__traceback__)))
        print("The above exception occured")

def read_code(rom : bytes, position : int, level = 0, visited = set()) -> int: # https://gbdev.io/pandocs/CPU_Instruction_Set.html
    while position < len(rom) and position not in visited:
        visited.add(position)
        match rom[position]:
            case 0x00:
                print(level, hex(position), "NOP")
            case 0x01:
                print(level, hex(position), "LD BC n16", rom[position+1:position+3].hex())
                position += 2
            case 0x02:
                print(level, hex(position), "LD BC A")
            case 0x03:
                print(level, hex(position), "INC BC")
            case 0x04:
                print(level, hex(position), "INC B")
            case 0x05:
                print(level, hex(position), "DEC B")
            case 0x06:
                print(level, hex(position), "LD B n8", rom[position+1:position+2].hex())
                position += 1
            case 0x07:
                print(level, hex(position), "RLCA")
            case 0x08:
                print(level, hex(position), "LD a16 SP", rom[position+1:position+3].hex())
                position += 2
            case 0x09:
                print(level, hex(position), "ADD HL BC")
            case 0x0A:
                print(level, hex(position), "LD A BC")
            case 0x0B:
                print(level, hex(position), "DEC BC")
            case 0x0C:
                print(level, hex(position), "INC C")
            case 0x0D:
                print(level, hex(position), "DEC C")
            case 0x0E:
                print(level, hex(position), "LD C n8", rom[position+1:position+2].hex())
                position += 1
            case 0x0F:
                print(level, hex(position), "RRCA")
            case 0x10:
                print(level, hex(position), "STOP")
                return 0
            case 0x11:
                print(level, hex(position), "LD DE n16", rom[position+1:position+3].hex())
                position += 2
            case 0x12:
                print(level, hex(position), "LD DE A")
            case 0x13:
                print(level, hex(position), "INC DE")
            case 0x14:
                print(level, hex(position), "INC D")
            case 0x15:
                print(level, hex(position), "DEC D")
            case 0x16:
                print(level, hex(position), "LD D n8", rom[position+1:position+2].hex())
                position += 1
            case 0x17:
                print(level, hex(position), "RLA")
            case 0x18:
                print(level, hex(position), "JR e8", rom[position+1:position+2].hex())
                read_code(rom, int.from_bytes(rom[position+1:position+2]), level+1, visited)
                position += 1
            case 0x19:
                print(level, hex(position), "ADD HL DE")
            case 0x1A:
                print(level, hex(position), "LD A DE")
            case 0x1B:
                print(level, hex(position), "DEC DE")
            case 0x1C:
                print(level, hex(position), "INC E")
            case 0x1D:
                print(level, hex(position), "DEC E")
            case 0x1E:
                print(level, hex(position), "LD E n8", rom[position+1:position+2].hex())
                position += 1
            case 0x1F:
                print(level, hex(position), "RRA")
            case 0x20:
                print(level, hex(position), "JR NZ e8", rom[position+1:position+2].hex())
                read_code(rom, int.from_bytes(rom[position+1:position+2]), level+1, visited)
                position += 1
            case 0x21:
                print(level, hex(position), "LD HL n16", rom[position+1:position+3].hex())
                position += 2
            case 0x22:
                print(level, hex(position), "LD HL+ A")
            case 0x23:
                print(level, hex(position), "INC HL")
            case 0x24:
                print(level, hex(position), "INC H")
            case 0x25:
                print(level, hex(position), "DEC H")
            case 0x26:
                print(level, hex(position), "LD H n8", rom[position+1:position+2].hex())
                position += 1
            case 0x27:
                print(level, hex(position), "D4A")
            case 0x28:
                print(level, hex(position), "JR Z e8", rom[position+1:position+2].hex())
                read_code(rom, int.from_bytes(rom[position+1:position+2]), level+1, visited)
                position += 1
            case 0x29:
                print(level, hex(position), "ADD HL HL")
            case 0x2A:
                print(level, hex(position), "LD A HL+")
            case 0x2B:
                print(level, hex(position), "DEC HL")
            case 0x2C:
                print(level, hex(position), "INC L")
            case 0x2D:
                print(level, hex(position), "DEC L")
            case 0x2E:
                print(level, hex(position), "LD L n8", rom[position+1:position+2].hex())
                position += 1
            case 0x2F:
                print(level, hex(position), "CPL")
            case 0x30:
                print(level, hex(position), "JR NC e8", rom[position+1:position+2].hex())
                read_code(rom, int.from_bytes(rom[position+1:position+2]), level+1, visited)
                position += 1
            case 0x31:
                print(level, hex(position), "LD SP n16", rom[position+1:position+3].hex())
                position += 2
            case 0x32:
                print(level, hex(position), "LD HL- A")
            case 0x33:
                print(level, hex(position), "INC SP")
            case 0x34:
                print(level, hex(position), "INC HL")
            case 0x35:
                print(level, hex(position), "DEC HL")
            case 0x36:
                print(level, hex(position), "LD HL n8", rom[position+1:position+2].hex())
                position += 1
            case 0x37:
                print(level, hex(position), "SCF")
            case 0x38:
                print(level, hex(position), "JR C e8", rom[position+1:position+2].hex())
                read_code(rom, int.from_bytes(rom[position+1:position+2]), level+1, visited)
                position += 1
            case 0x39:
                print(level, hex(position), "ADD HL SP")
            case 0x3A:
                print(level, hex(position), "LD A HL-")
            case 0x3B:
                print(level, hex(position), "DEC SP")
            case 0x3C:
                print(level, hex(position), "INC A")
            case 0x3D:
                print(level, hex(position), "DEC A")
            case 0x3E:
                print(level, hex(position), "LD A n8", rom[position+1:position+2].hex())
                position += 1
            case 0x3F:
                print(level, hex(position), "CCF")
            case 0x40:
                print(level, hex(position), "LD B B")
            case 0x41:
                print(level, hex(position), "LD B C")
            case 0x42:
                print(level, hex(position), "LD B D")
            case 0x43:
                print(level, hex(position), "LD B E")
            case 0x43:
                print(level, hex(position), "LD B H")
            case 0x45:
                print(level, hex(position), "LD B L")
            case 0x46:
                print(level, hex(position), "LD B HL")
            case 0x47:
                print(level, hex(position), "LD B A")
            case 0x48:
                print(level, hex(position), "LD C B")
            case 0x49:
                print(level, hex(position), "LD C C")
            case 0x4A:
                print(level, hex(position), "LD C D")
            case 0x4B:
                print(level, hex(position), "LD C E")
            case 0x4C:
                print(level, hex(position), "LD C H")
            case 0x4D:
                print(level, hex(position), "LD C L")
            case 0x4E:
                print(level, hex(position), "LD C HL")
            case 0x4F:
                print(level, hex(position), "LD C A")
            case 0x50:
                print(level, hex(position), "LD D B")
            case 0x51:
                print(level, hex(position), "LD D C")
            case 0x52:
                print(level, hex(position), "LD D D")
            case 0x53:
                print(level, hex(position), "LD D E")
            case 0x54:
                print(level, hex(position), "LD D H")
            case 0x55:
                print(level, hex(position), "LD D L")
            case 0x56:
                print(level, hex(position), "LD D HL")
            case 0x57:
                print(level, hex(position), "LD D A")
            case 0x58:
                print(level, hex(position), "LD E B")
            case 0x59:
                print(level, hex(position), "LD E C")
            case 0x5A:
                print(level, hex(position), "LD E D")
            case 0x5B:
                print(level, hex(position), "LD E E")
            case 0x5C:
                print(level, hex(position), "LD E H")
            case 0x5D:
                print(level, hex(position), "LD E L")
            case 0x5E:
                print(level, hex(position), "LD E HL")
            case 0x5F:
                print(level, hex(position), "LD E A")
            case 0x60:
                print(level, hex(position), "LD H B")
            case 0x61:
                print(level, hex(position), "LD H C")
            case 0x62:
                print(level, hex(position), "LD H D")
            case 0x63:
                print(level, hex(position), "LD H E")
            case 0x63:
                print(level, hex(position), "LD H H")
            case 0x65:
                print(level, hex(position), "LD H L")
            case 0x66:
                print(level, hex(position), "LD H HL")
            case 0x67:
                print(level, hex(position), "LD H A")
            case 0x68:
                print(level, hex(position), "LD L B")
            case 0x69:
                print(level, hex(position), "LD L C")
            case 0x6A:
                print(level, hex(position), "LD L D")
            case 0x6B:
                print(level, hex(position), "LD L E")
            case 0x6C:
                print(level, hex(position), "LD L H")
            case 0x6D:
                print(level, hex(position), "LD L L")
            case 0x6E:
                print(level, hex(position), "LD L HL")
            case 0x6F:
                print(level, hex(position), "LD L A")
            case 0x70:
                print(level, hex(position), "LD HL B")
            case 0x71:
                print(level, hex(position), "LD HL C")
            case 0x72:
                print(level, hex(position), "LD HL D")
            case 0x73:
                print(level, hex(position), "LD HL E")
            case 0x73:
                print(level, hex(position), "LD HL H")
            case 0x75:
                print(level, hex(position), "LD HL L")
            case 0x76:
                print(level, hex(position), "HALT")
            case 0x77:
                print(level, hex(position), "LD HL A")
            case 0x78:
                print(level, hex(position), "LD A B")
            case 0x79:
                print(level, hex(position), "LD A C")
            case 0x7A:
                print(level, hex(position), "LD A D")
            case 0x7B:
                print(level, hex(position), "LD A E")
            case 0x7C:
                print(level, hex(position), "LD A H")
            case 0x7D:
                print(level, hex(position), "LD A L")
            case 0x7E:
                print(level, hex(position), "LD A HL")
            case 0x7F:
                print(level, hex(position), "LD A A")
            case 0x80:
                print(level, hex(position), "ADD A B")
            case 0x81:
                print(level, hex(position), "ADD A C")
            case 0x82:
                print(level, hex(position), "ADD A D")
            case 0x83:
                print(level, hex(position), "ADD A E")
            case 0x83:
                print(level, hex(position), "ADD A H")
            case 0x85:
                print(level, hex(position), "ADD A L")
            case 0x86:
                print(level, hex(position), "ADD A HL")
            case 0x87:
                print(level, hex(position), "ADD A A")
            case 0x88:
                print(level, hex(position), "ADC A B")
            case 0x89:
                print(level, hex(position), "ADC A C")
            case 0x8A:
                print(level, hex(position), "ADC A D")
            case 0x8B:
                print(level, hex(position), "ADC A E")
            case 0x8C:
                print(level, hex(position), "ADC A H")
            case 0x8D:
                print(level, hex(position), "ADC A L")
            case 0x8E:
                print(level, hex(position), "ADC A HL")
            case 0x8F:
                print(level, hex(position), "ADC A A")
            case 0x90:
                print(level, hex(position), "SUB A B")
            case 0x91:
                print(level, hex(position), "SUB A C")
            case 0x92:
                print(level, hex(position), "SUB A D")
            case 0x93:
                print(level, hex(position), "SUB A E")
            case 0x93:
                print(level, hex(position), "SUB A H")
            case 0x95:
                print(level, hex(position), "SUB A L")
            case 0x96:
                print(level, hex(position), "SUB A HL")
            case 0x97:
                print(level, hex(position), "SUB A A")
            case 0x98:
                print(level, hex(position), "SBC A B")
            case 0x99:
                print(level, hex(position), "SBC A C")
            case 0x9A:
                print(level, hex(position), "SBC A D")
            case 0x9B:
                print(level, hex(position), "SBC A E")
            case 0x9C:
                print(level, hex(position), "SBC A H")
            case 0x9D:
                print(level, hex(position), "SBC A L")
            case 0x9E:
                print(level, hex(position), "SBC A HL")
            case 0x9F:
                print(level, hex(position), "SBC A A")
            case 0xA0:
                print(level, hex(position), "AND A B")
            case 0xA1:
                print(level, hex(position), "AND A C")
            case 0xA2:
                print(level, hex(position), "AND A D")
            case 0xA3:
                print(level, hex(position), "AND A E")
            case 0xA3:
                print(level, hex(position), "AND A H")
            case 0xA5:
                print(level, hex(position), "AND A L")
            case 0xA6:
                print(level, hex(position), "AND A HL")
            case 0xA7:
                print(level, hex(position), "AND A A")
            case 0xA8:
                print(level, hex(position), "XOR A B")
            case 0xA9:
                print(level, hex(position), "XOR A C")
            case 0xAA:
                print(level, hex(position), "XOR A D")
            case 0xAB:
                print(level, hex(position), "XOR A E")
            case 0xAC:
                print(level, hex(position), "XOR A H")
            case 0xAD:
                print(level, hex(position), "XOR A L")
            case 0xAE:
                print(level, hex(position), "XOR A HL")
            case 0xAF:
                print(level, hex(position), "XOR A A")
            case 0xB0:
                print(level, hex(position), "OR A B")
            case 0xB1:
                print(level, hex(position), "OR A C")
            case 0xB2:
                print(level, hex(position), "OR A D")
            case 0xB3:
                print(level, hex(position), "OR A E")
            case 0xB3:
                print(level, hex(position), "OR A H")
            case 0xB5:
                print(level, hex(position), "OR A L")
            case 0xB6:
                print(level, hex(position), "OR A HL")
            case 0xB7:
                print(level, hex(position), "OR A A")
            case 0xB8:
                print(level, hex(position), "CP A B")
            case 0xB9:
                print(level, hex(position), "CP A C")
            case 0xBA:
                print(level, hex(position), "CP A D")
            case 0xBB:
                print(level, hex(position), "CP A E")
            case 0xBC:
                print(level, hex(position), "CP A H")
            case 0xBD:
                print(level, hex(position), "CP A L")
            case 0xBE:
                print(level, hex(position), "CP A HL")
            case 0xBF:
                print(level, hex(position), "CP A A")
            case 0xC0:
                print(level, hex(position), "RET NZ")
                return
            case 0xC1:
                print(level, hex(position), "POP BC")
            case 0xC2:
                print(level, hex(position), "JP NZ a16", rom[position+1:position+3].hex())
                read_code(rom, int.from_bytes(rom[position+1:position+3]), level+1, visited)
                position += 2
            case 0xC3:
                print(level, hex(position), "JP a16", rom[position+1:position+3].hex())
                read_code(rom, int.from_bytes(rom[position+1:position+3]), level+1, visited)
                position += 2
            case 0xC4:
                print(level, hex(position), "CALL NZ a16", rom[position+1:position+3].hex())
                read_code(rom, int.from_bytes(rom[position+1:position+3]), level+1, visited)
                position += 2
            case 0xC5:
                print(level, hex(position), "PUSH BC")
            case 0xC6:
                print(level, hex(position), "ADD A n8", rom[position+1:position+2].hex())
                position += 1
            case 0xC7:
                print(level, hex(position), "RST $00")
            case 0xC8:
                print(level, hex(position), "RET Z")
                return
            case 0xC9:
                print(level, hex(position), "RET")
                return
            case 0xCA:
                print(level, hex(position), "JP Z a16", rom[position+1:position+3].hex())
                read_code(rom, int.from_bytes(rom[position+1:position+3]), level+1, visited)
                position += 2
            case 0xCB:
                print(level, hex(position), "PREFIX", rom[position+1:position+3].hex())
                position += 2
            case 0xCC:
                print(level, hex(position), "CALL Z a16", rom[position+1:position+3].hex())
                read_code(rom, int.from_bytes(rom[position+1:position+3]), level+1, visited)
                position += 2
            case 0xCD:
                print(level, hex(position), "CALL a16", rom[position+1:position+3].hex())
                read_code(rom, int.from_bytes(rom[position+1:position+3]), level+1, visited)
                position += 2
            case 0xCE:
                print(level, hex(position), "ADC A n8", rom[position+1:position+2].hex())
                position += 1
            case 0xCF:
                print(level, hex(position), "RST $08")
            case 0xD0:
                print(level, hex(position), "RET NC")
                return
            case 0xD1:
                print(level, hex(position), "POP DE")
            case 0xD2:
                print(level, hex(position), "JP NC a16", rom[position+1:position+3].hex())
                read_code(rom, int.from_bytes(rom[position+1:position+3]), level+1, visited)
                position += 2
            case 0xD4:
                print(level, hex(position), "CALL NC a16", rom[position+1:position+3].hex())
                read_code(rom, int.from_bytes(rom[position+1:position+3]), level+1, visited)
                position += 2
            case 0xD5:
                print(level, hex(position), "PUSH DE")
            case 0xD6:
                print(level, hex(position), "SUB A n8", rom[position+1:position+2].hex())
                position += 1
            case 0xD7:
                print(level, hex(position), "RST $10")
            case 0xD8:
                print(level, hex(position), "RET C")
                return
            case 0xD9:
                print(level, hex(position), "RETI")
                return
            case 0xDA:
                print(level, hex(position), "JP C a16", rom[position+1:position+3].hex())
                read_code(rom, int.from_bytes(rom[position+1:position+3]), level+1, visited)
                position += 2
            case 0xDC:
                print(level, hex(position), "CALL C a16", rom[position+1:position+3].hex())
                read_code(rom, int.from_bytes(rom[position+1:position+3]), level+1, visited)
                position += 2
            case 0xDE:
                print(level, hex(position), "SBC A n8", rom[position+1:position+2].hex())
                position += 1
            case 0xDF:
                print(level, hex(position), "RST $18")
            case 0xE0:
                print(level, hex(position), "LDH a8 A", rom[position+1:position+2].hex())
                position += 1
            case 0xE1:
                print(level, hex(position), "POP HL")
            case 0xE2:
                print(level, hex(position), "LD C A")
            case 0xE5:
                print(level, hex(position), "PUSH HL")
            case 0xE6:
                print(level, hex(position), "ADD A n8", rom[position+1:position+2].hex())
                position += 1
            case 0xE7:
                print(level, hex(position), "RST $20")
            case 0xE8:
                print(level, hex(position), "ADD SP e8", rom[position+1:position+2].hex())
                position += 1
            case 0xE9:
                print(level, hex(position), "JP HL")
            case 0xEA:
                print(level, hex(position), "LD a16 A", rom[position+1:position+3].hex())
                position += 2
            case 0xEE:
                print(level, hex(position), "XOR A n8", rom[position+1:position+2].hex())
                position += 1
            case 0xEF:
                print(level, hex(position), "RST $28")
            case 0xF0:
                print(level, hex(position), "LDH A a8", rom[position+1:position+2].hex())
                position += 1
            case 0xF1:
                print(level, hex(position), "POP AF")
            case 0xF2:
                print(level, hex(position), "LD A C")
            case 0xF3:
                print(level, hex(position), "DI")
            case 0xF5:
                print(level, hex(position), "PUSH AF")
            case 0xF6:
                print(level, hex(position), "OR A n8", rom[position+1:position+2].hex())
                position += 1
            case 0xF7:
                print(level, hex(position), "RST $30")
            case 0xF8:
                print(level, hex(position), "LD HL SP + e8", rom[position+1:position+2].hex())
                position += 1
            case 0xF9:
                print(level, hex(position), "LD SP HL")
            case 0xFA:
                print(level, hex(position), "LD A a16", rom[position+1:position+3].hex())
                position += 2
            case 0xFB:
                print(level, hex(position), "EI")
            case 0xFE:
                print(level, hex(position), "C A n8", rom[position+1:position+2].hex())
                position += 1
            case 0xFF:
                print(level, hex(position), "RST $38")
            case _:
                raise Exception("{} {} Unknown opcode {}".format(level, hex(position), rom[position:position+1].hex()))
        position += 1

def run(path : str) -> None:
    rom_headers = check_rom(path)
    if rom_headers["valid_file"]:
        test_read_opcodes(rom_headers)

if __name__ == "__main__":
    run("Donkey Kong.gb")