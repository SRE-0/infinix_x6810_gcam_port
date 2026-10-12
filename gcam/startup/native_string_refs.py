"""Find AArch64 ADRP page references to selected native strings (read-only).

This is a syntactic reference search, not a complete disassembler or call graph.
"""
import argparse
from pathlib import Path
import struct
from elftools.elf.elffile import ELFFile
from capstone import Cs, CS_ARCH_ARM64, CS_MODE_LITTLE_ENDIAN

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('elf', type=Path)
p.add_argument('text')
a = p.parse_args()
with a.elf.open('rb') as f:
    elf = ELFFile(f)
    loads = [s for s in elf.iter_segments() if s['p_type'] == 'PT_LOAD']
    raw = a.elf.read_bytes()
    offset = 0
    targets = []
    while (offset := raw.find(a.text.encode(), offset)) >= 0:
        s = next(s for s in loads if s['p_offset'] <= offset < s['p_offset']+s['p_filesz'])
        address = s['p_vaddr'] + offset - s['p_offset']
        print('STRING', hex(address), repr(raw[offset:raw.find(b'\0',offset)].decode(errors='replace')))
        targets.append(address & ~4095)
        offset += 1
    code = elf.get_section_by_name('.text')
    data = code.data()
    origin = code['sh_addr']
    md = Cs(CS_ARCH_ARM64, CS_MODE_LITTLE_ENDIAN)
    for i, (ins,) in enumerate(struct.iter_unpack('<I',data[:len(data)//4*4])):
        if ins & 0x9f000000 != 0x90000000:
            continue
        imm = ((ins >> 29) & 3) | (((ins >> 5) & 0x7ffff) << 2)
        if imm & (1 << 20):
            imm -= 1 << 21
        pc = origin+i*4
        page = (pc & ~4095) + imm*4096
        if page in targets:
            print('REFERENCE',hex(pc))
            for instruction in md.disasm(data[max(0,i*4-12):i*4+36],pc-12):
                print(hex(instruction.address),instruction.mnemonic,instruction.op_str)
