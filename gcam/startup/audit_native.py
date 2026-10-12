"""Inspect exported JNI segmenter code in a user-extracted ELF; no writes."""
import argparse
from pathlib import Path
import sys

p = argparse.ArgumentParser(description=__doc__)
p.add_argument("--deps", type=Path, required=True)
p.add_argument("elf", type=Path)
p.add_argument("--address", type=lambda s: int(s, 0))
p.add_argument("--bytes", type=int, default=1000)
a = p.parse_args()
sys.path.insert(0, str(a.deps.resolve()))
from elftools.elf.elffile import ELFFile
from capstone import Cs, CS_ARCH_ARM64, CS_MODE_LITTLE_ENDIAN

with a.elf.open("rb") as f:
    e = ELFFile(f)
    segments = [s for s in e.iter_segments() if s["p_type"] == "PT_LOAD"]
    md = Cs(CS_ARCH_ARM64, CS_MODE_LITTLE_ENDIAN)
    if a.address is not None:
        address = a.address
        segment = next(x for x in segments if x["p_vaddr"] <= address < x["p_vaddr"] + x["p_filesz"])
        f.seek(segment["p_offset"] + address - segment["p_vaddr"])
        for instruction in md.disasm(f.read(a.bytes), address):
            print(hex(instruction.address), instruction.mnemonic, instruction.op_str)
        raise SystemExit(0)
    for s in e.get_section_by_name(".dynsym").iter_symbols():
        if "NativePortraitSegmenterInterface" not in s.name:
            continue
        address = s["st_value"]
        print(s.name, hex(address), s["st_size"])
        segment = next(x for x in segments if x["p_vaddr"] <= address < x["p_vaddr"] + x["p_filesz"])
        f.seek(segment["p_offset"] + address - segment["p_vaddr"])
        for instruction in md.disasm(f.read(min(s["st_size"], 1200)), address):
            print(hex(instruction.address), instruction.mnemonic, instruction.op_str)
