import glob, os, struct, hashlib, json, sys

ROOT = sys.argv[1]

def parse_elf(data):
    d = data
    cls = d[4]
    out = {
        "class": "ELF32" if cls == 1 else ("ELF64" if cls == 2 else "?"),
        "endian": "LE" if d[5] == 1 else "BE",
    }
    if cls == 1:
        e_type, e_machine, _ = struct.unpack_from("<HHI", d, 16)
        e_entry = struct.unpack_from("<I", d, 24)[0]
        e_phoff = struct.unpack_from("<I", d, 28)[0]
        e_flags = struct.unpack_from("<I", d, 36)[0]
        e_ehsize, e_phentsize, e_phnum = struct.unpack_from("<HHH", d, 40)
    else:
        e_type, e_machine, _ = struct.unpack_from("<HHI", d, 16)
        e_entry = struct.unpack_from("<Q", d, 24)[0]
        e_phoff = struct.unpack_from("<Q", d, 32)[0]
        e_flags = struct.unpack_from("<I", d, 48)[0]
        e_ehsize, e_phentsize, e_phnum = struct.unpack_from("<HHH", d, 52)
    out["e_type"] = e_type
    out["machine"] = "0x%x" % e_machine
    out["entry"] = "0x%x" % e_entry
    out["phoff"] = e_phoff
    out["phnum"] = e_phnum
    out["flags"] = hex(e_flags)
    segs = []
    if e_phoff and e_phnum and e_phentsize and e_phoff + e_phentsize * e_phnum <= len(d):
        for i in range(e_phnum):
            ph = d[e_phoff + i * e_phentsize : e_phoff + (i + 1) * e_phentsize]
            if len(ph) < e_phentsize:
                break
            if cls == 1:
                p_type, p_offset, p_vaddr = struct.unpack_from("<III", ph, 0)
                p_paddr, p_filesz, p_memsz, p_flags, p_align = struct.unpack_from("<IIIII", ph, 12)
            else:
                p_type, p_flags = struct.unpack_from("<II", ph, 0)
                p_offset, p_vaddr, p_paddr, p_filesz, p_memsz, p_align = struct.unpack_from("<QQQQQQ", ph, 8)
            segs.append(
                {
                    "type": p_type,
                    "vaddr": "0x%x" % p_vaddr,
                    "paddr": "0x%x" % p_paddr,
                    "filesz": p_filesz,
                    "memsz": p_memsz,
                    "flags": p_flags,
                    "offset": p_offset,
                }
            )
    out["phdrs"] = segs
    return out


def describe(name, data):
    r = {"name": name, "size": len(data), "magic": data[:4].hex(), "sha256": hashlib.sha256(data).hexdigest()}
    if data[:4] == b"\x7fELF":
        r["kind"] = "ELF"
        r.update(parse_elf(data))
    elif data[:4] in (b"MBN\x00", b"MBN!", b"MBN\x01"):
        r["kind"] = "MBN"
        r["mbn_sig"] = data[:4].hex()
    else:
        r["kind"] = "RAW"
        r["head16"] = data[:16].hex()
    return r


for rev in ("r7", "r9"):
    bldir = os.path.join(ROOT, "firmware", "extracted", rev, "BL")
    modules = []
    for f in sorted(os.listdir(bldir)):
        full = os.path.join(bldir, f)
        if not os.path.isfile(full) or f.endswith(".lz4"):
            continue
        modules.append(describe(f, open(full, "rb").read()))
    outpath = os.path.join(ROOT, "analysis", "01-source", rev, "bl-modules.json")
    with open(outpath, "w") as jf:
        json.dump({"rev": rev, "modules": modules}, jf, indent=2)
    print("== %s: %d decompressed modules ==" % (rev, len(modules)))
    for m in modules:
        if m["kind"] == "ELF":
            seg0 = m["phdrs"][0] if m["phdrs"] else {}
            print(
                "  %-30s ELF%s ent=%-16s phnum=%d first=%s"
                % (m["name"], m["class"], m["entry"], m["phnum"], seg0.get("vaddr", "-"))
            )
        else:
            print("  %-30s %-4s %10d" % (m["name"], m["kind"], m["size"]))