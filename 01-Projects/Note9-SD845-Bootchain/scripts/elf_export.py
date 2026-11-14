#!/usr/bin/env python3
"""elf_export.py — capstone-based function export matching the ExportFunctions.java
JSON contract (docs/02 §2 Stage B) without requiring Ghidra.

Output contract per image:
  image: {file, name, rev, base, language, sha256}
  functions: [{name, addr, size, blocks, mnemonics{...}, calls[...], constants[...]}]

Function discovery: ELF .symtab/.dynsym STT_FUNC symbols carrying a size. Where the
image has no usable symtab (stripped/secured), functions fall back to a linear sweep
over executable segments (see --force-sweep). Same contract either way.

stdlib + capstone only.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import struct
import sys
from pathlib import Path

import capstone

# --- ELF parsing ------------------------------------------------------------

SHT_SYMTAB, SHT_DYNSYM, SHT_STRTAB = 2, 11, 3
STT_FUNC = 2
PT_LOAD = 1


def parse_elf(data: bytes) -> dict:
    if data[:4] != b"\x7fELF":
        raise ValueError("not an ELF file")
    is64 = data[4] == 2
    le = data[5] == 1
    e = "<" if le else ">"
    out = {"is64": is64, "little": le}
    mach, = struct.unpack_from(e + "H", data, 18)
    out["machine"] = mach
    if is64:
        out["entry"] = struct.unpack_from(e + "Q", data, 24)[0]
        out["phoff"], out["shoff"] = struct.unpack_from(e + "QQ", data, 32)
        out["ehsize"], out["phentsize"], out["phnum"] = struct.unpack_from(e + "HHH", data, 52)
        out["shentsize"], out["shnum"], out["shstrndx"] = struct.unpack_from(e + "HHH", data, 58)
    else:
        out["entry"] = struct.unpack_from(e + "I", data, 24)[0]
        out["phoff"], out["shoff"] = struct.unpack_from(e + "II", data, 28)
        out["ehsize"], out["phentsize"], out["phnum"] = struct.unpack_from(e + "HHH", data, 40)
        out["shentsize"], out["shnum"], out["shstrndx"] = struct.unpack_from(e + "HHH", data, 46)
    return out


def read_shdrs(data: bytes, h: dict) -> list[dict]:
    e = "<" if h["little"] else ">"
    shdrs = []
    if not h["shoff"] or not h["shnum"]:
        return shdrs
    for i in range(h["shnum"]):
        off = h["shoff"] + i * h["shentsize"]
        rec = data[off : off + h["shentsize"]]
        if h["is64"]:
            sh_name, sh_type = struct.unpack_from(e + "II", rec, 0)
            sh_flags, sh_addr, sh_offset, sh_size = struct.unpack_from(e + "QQQQ", rec, 8)
            sh_link, sh_info, sh_addralign, sh_entsize = struct.unpack_from(e + "QQQQ", rec, 40)
        else:
            sh_name, sh_type, sh_flags = struct.unpack_from(e + "III", rec, 0)
            sh_addr, sh_offset, sh_size = struct.unpack_from(e + "III", rec, 12)
            sh_link, sh_info, sh_addralign, sh_entsize = struct.unpack_from(e + "III", rec, 24)
        shdrs.append(dict(type=sh_type, addr=sh_addr, offset=sh_offset,
                          size=sh_size, link=sh_link, info=sh_info, name=sh_name))
    # resolve section names
    if h["shstrndx"] < len(shdrs):
        s = shdrs[h["shstrndx"]]
        strtab = data[s["offset"] : s["offset"] + s["size"]]
        for sd in shdrs:
            if 0 <= sd["name"] < len(strtab):
                end = strtab.find(b"\0", sd["name"])
                sd["str"] = strtab[sd["name"] : end].decode("latin-1")
            else:
                sd["str"] = "?"
    return shdrs


def read_phdrs(data: bytes, h: dict) -> list[dict]:
    e = "<" if h["little"] else ">"
    phdrs = []
    if not h["phoff"] or not h["phnum"]:
        return phdrs
    for i in range(h["phnum"]):
        off = h["phoff"] + i * h["phentsize"]
        rec = data[off : off + h["phentsize"]]
        if h["is64"]:
            p_type, p_flags = struct.unpack_from(e + "II", rec, 0)
            p_offset, p_vaddr, p_paddr, p_filesz, p_memsz, p_align = struct.unpack_from(e + "QQQQQQ", rec, 8)
        else:
            p_type, p_offset, p_vaddr = struct.unpack_from(e + "III", rec, 0)
            p_paddr, p_filesz, p_memsz, p_flags, p_align = struct.unpack_from(e + "IIIII", rec, 12)
        phdrs.append(dict(type=p_type, offset=p_offset, vaddr=p_vaddr,
                          filesz=p_filesz, memsz=p_memsz, flags=p_flags))
    return phdrs


def load_map(phdrs: list[dict]) -> callable:
    """vaddr -> file offset for any loaded byte (PT_LOAD only)."""
    loads = [p for p in phdrs if p["type"] == PT_LOAD]
    def _off(vaddr):
        for p in loads:
            if p["vaddr"] <= vaddr < p["vaddr"] + p["filesz"]:
                return p["offset"] + (vaddr - p["vaddr"])
        return None
    return _off


def read_strtab(data: bytes, shdrs: list[dict], link: int) -> dict:
    if not (0 <= link < len(shdrs)):
        return {}
    s = shdrs[link]
    raw = data[s["offset"] : s["offset"] + s["size"]]
    return {i: nm for i, nm in enumerate(raw.split(b"\0")) if nm}


def read_symtab(data: bytes, h: dict, sh: dict, shdrs: list[dict]) -> list[dict]:
    e = "<" if h["little"] else ">"
    entsize = sh["entsize"] or (24 if h["is64"] else 16)
    names = read_strtab(data, shdrs, sh["link"])
    syms = []
    for i in range(sh["size"] // entsize):
        off = sh["offset"] + i * entsize
        rec = data[off : off + entsize]
        if h["is64"]:
            st_name, st_info, st_other, st_shndx = struct.unpack_from(e + "IBBH", rec, 0)
            st_value, st_size = struct.unpack_from(e + "QQ", rec, 8)
        else:
            st_name, st_value, st_size = struct.unpack_from(e + "III", rec, 0)
            st_info, st_other, st_shndx = struct.unpack_from(e + "BBH", rec, 12)
        syms.append(dict(name=names.get(st_name, "?"), value=st_value,
                         size=st_size, info=st_info, shndx=st_shndx))
    return syms


def function_symbols(data: bytes, h: dict, shdrs: list[dict]) -> list[dict]:
    out = []
    for sh in shdrs:
        if sh.get("type") in (SHT_SYMTAB, SHT_DYNSYM):
            for s in read_symtab(data, h, sh, shdrs):
                if (s["info"] >> 4) == STT_FUNC and s["size"] > 0 and s["value"]:
                    out.append(s)
    return out


# --- disassembly ------------------------------------------------------------

def make_md(arch: str):
    """Return a capstone Cs configured for the image's instruction set."""
    if arch == "thumb":
        md = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_THUMB + capstone.CS_MODE_LITTLE_ENDIAN)
    elif arch == "a32":
        md = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM + capstone.CS_MODE_LITTLE_ENDIAN)
    else:  # a64
        md = capstone.Cs(capstone.CS_ARCH_ARM64, capstone.CS_MODE_ARM)
    md.detail = True
    return md


def arch_for(h: dict) -> str:
    """e_machine -> instruction-set tag used for disassembly."""
    return "thumb" if h["machine"] == 40 else "a64"


def _arch_language(arch: str) -> str:
    return {"a64": "aarch64:LE:64:v8A",
            "thumb": "arm:LE:32:Thumb",
            "a32": "arm:LE:32:A32"}[arch]


def _branch_operands_calls(ins, arch: str):
    """Return (calls:[str target], imms:[int]) for one decoded instruction."""
    if arch == "a64":
        if ins.mnemonic not in ("bl", "b"):
            return [], []
        tgt = None
        for op in ins.operands:
            if op.type in (capstone.arm64.ARM64_OP_IMM, capstone.arm64.ARM64_OP_CIMM):
                tgt = op.imm
        return ([tgt] if tgt is not None else []), []
    # arm (thumb/a32): bl/b/blx carry the absolute target in op.imm
    if ins.mnemonic not in ("bl", "b", "blx"):
        return [], []
    tgt = None
    for op in ins.operands:
        if op.type in (2, 4):  # ARM_OP_IMM / ARM_OP_CIMM
            tgt = op.imm
    return ([tgt] if tgt is not None else []), []


def scan_funcs(off: callable, data: bytes, funcs: list[dict], arch: str = "a64") -> list[dict]:
    """Disassemble each function, build the contract fields."""
    if not funcs:
        return []
    md = make_md(arch)
    if arch == "a64":
        imm_types = (capstone.arm64.ARM64_OP_IMM, capstone.arm64.ARM64_OP_CIMM)
    else:
        imm_types = (2, 4)
    by_addr = sorted({f["value"] for f in funcs})
    # symbol resolution for call targets: nearest preceding symbol
    targets = sorted(set(by_addr) | {f["value"] + f["size"] for f in funcs})

    def resolve(addr):
        best, bestd = None, None
        for t in targets:
            d = addr - t
            if 0 <= d and (bestd is None or d < bestd):
                best, bestd = t, d
        return best if best is not None and bestd < 0x20 else None

    results = []
    for f in sorted(funcs, key=lambda s: s["value"]):
        start, end = f["value"], f["value"] + f["size"]
        foff = off(start)
        if foff is None:
            continue
        code = data[foff : foff + f["size"]]
        mn = {}
        calls = []
        constants = []
        addr = start
        for ins in md.disasm(code, start):
            mn[ins.mnemonic] = mn.get(ins.mnemonic, 0) + 1
            br_calls, imms = _branch_operands_calls(ins, arch)
            for tgt in br_calls:
                if arch != "a64" and tgt is None:
                    tgt = addr + ins.size
                c = resolve(tgt) if tgt is not None else None
                calls.append("0x%x" % (c if c is not None else tgt))
            for op in ins.operands:
                if op.type in imm_types and (op.imm < 0 or op.imm >= 0x100):
                    constants.append(op.imm & 0xFFFFFFFFFFFFFFFF)
            addr += ins.size
        results.append(dict(
            name=f["name"], addr=start, size=f["size"], blocks=1,
            mnemonics=mn, calls=sorted(set(calls)), constants=sorted(set(constants))[:64],
            sha256=hashlib.sha256(code).hexdigest(),
        ))
    return results


def _prologue(md, code: bytes, addr: int) -> bool:
    """True if the 4-byte-aligned addr starts with a classic AArch64 prologue."""
    ins = list(md.disasm(code[:16], addr))
    if len(ins) < 2:
        return False
    i0 = ins[0]
    # canonical frame pointer: stp x29, x30, [sp,#-N]!  (writeback)
    if i0.mnemonic == "stp" and len(i0.operands) >= 3:
        rd1, rd2, base = i0.operands[0], i0.operands[1], i0.operands[2]
        if base.type == capstone.arm64.ARM64_OP_REG and base.reg == capstone.arm64.ARM64_REG_SP:
            if rd1.reg in (capstone.arm64.ARM64_REG_X29, capstone.arm64.ARM64_REG_W29):
                return True
        # plain stp sp-based without writeback also common
        if base.type == capstone.arm64.ARM64_OP_REG and base.reg == capstone.arm64.ARM64_REG_SP \
                and rd1.reg in (capstone.arm64.ARM64_REG_X29, capstone.arm64.ARM64_REG_W29):
            return True
    # leaf: sub sp, sp, #imm  (mov x29, sp at top implies frame func)
    if i0.mnemonic == "sub" and len(i0.operands) >= 3:
        o1 = i0.operands[0]
        if o1.type == capstone.arm64.ARM64_OP_REG and o1.reg == capstone.arm64.ARM64_REG_SP:
            return True
    if i0.mnemonic == "mov" and len(i0.operands) >= 2:
        o0, o1 = i0.operands[0], i0.operands[1]
        if o0.type == o1.type == capstone.arm64.ARM64_OP_REG \
                and o0.reg == capstone.arm64.ARM64_REG_X29 \
                and o1.reg == capstone.arm64.ARM64_REG_SP:
            return True
    return False


def detect_prologue_funcs(data: bytes, h: dict, phdrs: list[dict], off: callable) -> list[dict]:
    """Scan executable PT_LOAD segments for AArch64 prologues -> function starts.
    Bodies extend from one start to the next (or segment end); heuristic only —
    documented as such so the diff aligns structure, not recovered names."""
    md = capstone.Cs(capstone.CS_ARCH_ARM64, capstone.CS_MODE_ARM)
    md.detail = True
    starts = []
    for p in phdrs:
        if p["type"] != PT_LOAD or not (p["flags"] & 1):
            continue
        if not (p["filesz"] and p["vaddr"]):
            continue
        seg = data[p["offset"] : p["offset"] + p["filesz"]]
        for rva in range(0, len(seg) - 4, 4):
            a = p["vaddr"] + rva
            if _prologue(md, seg[rva:], a):
                starts.append((a, p))
    starts.sort(key=lambda s: s[0])
    funcs = []
    for i, (a, p) in enumerate(starts):
        seg_end = p["vaddr"] + p["filesz"]
        hard_end = starts[i + 1][0] if i + 1 < len(starts) else seg_end
        end = hard_end
        # terminate at first ret in linear sweep (bounded by hard_end)
        foff = off(a)
        if foff is not None:
            buf = data[foff : min(foff + (hard_end - a), foff + 0x4000)]
            lim = hard_end
            for ins in md.disasm(buf, a):
                if ins.mnemonic == "ret":
                    end = ins.address + ins.size
                    break
                if ins.address + ins.size >= lim:
                    break
        if end - a < 8:
            continue
        funcs.append(dict(name="f_%08x" % a, value=a, size=end - a))
    return funcs


BLOCK_SIZE = 256


def detect_block_funcs(data: bytes, h: dict, phdrs: list[dict]) -> list[dict]:
    """Uniform fixed-size block segmentation of executable PT_LOAD segments.

    Splits every executable segment into BLOCK_SIZE-byte, vaddr-aligned blocks and
    emits one synthetic func per non-empty block (pure zero-fill blocks are skipped —
    they carry no information and are skipped in every revision alike, keeping the
    block grid identical across revisions). Disassembly of each block happens later in
    scan_funcs() with the image's instruction set, so this detector is arch-agnostic.
    """
    funcs = []
    for p in phdrs:
        if p["type"] != PT_LOAD or not (p["flags"] & 1):
            continue
        if not p["filesz"]:
            continue
        seg = data[p["offset"] : p["offset"] + p["filesz"]]
        base = p["vaddr"]
        n = len(seg)
        for rva in range(0, n, BLOCK_SIZE):
            chunk = seg[rva : rva + BLOCK_SIZE]
            a = base + rva
            # every 256-byte window is emitted — zero-fill included — so the
            # block grid is identical across revisions by construction and any
            # tail-block size delta (segment grew/shrunk) shows up as a pair.
            funcs.append(dict(name="b_%08x" % a, value=a, size=len(chunk)))
    funcs.sort(key=lambda f: f["value"])
    return funcs


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="capstone ELF function export")
    ap.add_argument("--bin", required=True, help="path to ELF image (r7/r9)")
    ap.add_argument("--rev", required=True)
    ap.add_argument("--comp", required=True)
    ap.add_argument("--out", required=True, help="output json path")
    ap.add_argument("--mode", choices=("auto", "symtab", "prologue", "block"),
                    default="auto", help="function discovery (default: symtab, else block)")
    ap.add_argument("--arch", choices=("auto", "a64", "thumb", "a32"),
                    default="auto", help="instruction set (auto: e_machine)")
    args = ap.parse_args(argv)

    data = Path(args.bin).read_bytes()
    h = parse_elf(data)
    shdrs = read_shdrs(data, h)
    phdrs = read_phdrs(data, h)
    off = load_map(phdrs)
    arch = arch_for(h) if args.arch == "auto" else args.arch

    funcs, source = [], "none"
    if args.mode in ("auto", "symtab"):
        funcs = function_symbols(data, h, shdrs)
        if funcs:
            source = "symtab"
    if not funcs and args.mode in ("auto", "prologue") and arch == "a64":
        funcs = detect_prologue_funcs(data, h, phdrs, off)
        if funcs:
            source = "prologue"
    if not funcs and args.mode in ("auto", "block"):
        funcs = detect_block_funcs(data, h, phdrs)
        if funcs:
            source = f"block-{BLOCK_SIZE}"

    image = dict(
        file=str(Path(args.bin).name), name=Path(args.bin).stem,
        rev=args.rev, base=h["entry"],
        language=_arch_language(arch),
        sha256=hashlib.sha256(data).hexdigest(),
        sym_source=source,
    )
    funcs_out = scan_funcs(off, data, funcs, arch)
    out = {"image": image, "functions": funcs_out}
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(f"{args.comp}-{args.rev}: {len(funcs_out)} funcs from {source} -> {args.out}")
    return 0


def _sweep(h: dict, phdrs: list[dict]) -> list[dict]:
    """Fallback: one fake func per executable PT_LOAD (keeps diff meaningful)."""
    out = []
    for i, p in enumerate(phdrs):
        if p["type"] == PT_LOAD and p["flags"] & 1:  # X
            out.append(dict(name=f"seg{i}", value=p["vaddr"], size=p["filesz"], size0=p["filesz"]))
    return out


if __name__ == "__main__":
    sys.exit(main())