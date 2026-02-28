#!/usr/bin/env python3
# image_decrypter_v4.py (UI/UX + progress bar)

import os, sys, time, zlib, binascii, plistlib
import shutil

try:
    from PIL import Image
except Exception:
    Image = None

HOME = "/storage/emulated/0/ryanex"
ROOT = os.path.join(HOME, "proyek_pkct")

ASSETS_ORIGINAL = os.path.join(ROOT, "assets_original")
HASIL_ROOT      = os.path.join(ROOT, "hasil")
STEP1_DECODE   = os.path.join(HASIL_ROOT, "step1_decode_raw")
STEP2_PNG_OK   = os.path.join(HASIL_ROOT, "step2_image_valid")
EKSTRAK_PLIST   = os.path.join(HASIL_ROOT, "ekstrak_plist")
EKSTRAK_ATLAS   = os.path.join(HASIL_ROOT, "ekstrak_atlas")

PKCT_HDR = 12
EXTS_IMG = (".png", ".jpg", ".jpeg")

PNG_SIG  = b"\x89PNG\r\n\x1a\n"
PNG_TAIL = b"PNG\r\n\x1a\n"
JPG_TAIL = b"\xD8\xFF"

# ===== ANSI warna elegan =====
class C:

    RST = "\033[0m"
    DIM = "\033[2m"
    BLD = "\033[1m"
    CY  = "\033[36m"  # cyan = progress bar
    BL  = "\033[34m"  # blue = judul
    GN  = "\033[32m"
    YL  = "\033[33m"
    RD  = "\033[31m"
    GY  = "\033[90m"

def color(s, c):
    return f"{c}{s}{C.RST}"

def center_text(text, color_code):
    try:
        width = shutil.get_terminal_size().columns
    except Exception:
        width = 80
    return color(text.center(width), color_code)

def show_title():
    print()  # newline sebelum
    print()
    print(center_text("[ IMAGE ASSETS DECRYPTER ]", C.BLD + C.CY))
    print()

def show_footer():
    print()  # newline sebelum
    print()  # newline sebelum 
    print(center_text("2026 RyanEx, Inc.", C.BLD + "\033[38;5;250m"))
    print()
    print()

def ensure_dir(p):
    os.makedirs(p, exist_ok=True)

def hr(title):
    print("\n" + color("="*64, C.GY))
    print(color(title, C.BLD))
    print(color("="*64, C.GY))

# ===== Progress Bar =====
class ProgressBar:
    def __init__(self, total, label, width=28):
        self.total = max(1, int(total))
        self.label = label
        self.width = width
        self.start = time.time()
        self.last_draw = 0.0
        self.done_count = 0

    def _fmt_time(self, sec):
        sec = int(sec)
        m, s = divmod(sec, 60)
        h, m = divmod(m, 60)
        if h: return f"{h}j{m:02d}m"
        if m: return f"{m}m{s:02d}d"
        return f"{s}d"

    def update(self, done, extra=""):
        self.done_count = done
        now = time.time()
        # throttle refresh
        if now - self.last_draw < 0.05 and done < self.total:
            return
        self.last_draw = now

        pct = done / self.total
        filled = int(self.width * pct)
        bar = "█" * filled + "░" * (self.width - filled)

        elapsed = now - self.start
        rate = done / elapsed if elapsed > 0 else 0.0
        eta = (self.total - done) / rate if rate > 0 else 0.0

        line = (
            f"{color(self.label, C.BLD)} "
            f"{color(bar, C.CY)} "
            f"{color(f'{pct*100:5.1f}%', C.CY)} "
            f"{color(f'{done}/{self.total}', C.GY)} "
            f"{color('ETA', C.GY)} {color(self._fmt_time(eta), C.GY)} "
        )
        if extra:
            line += color(extra, C.DIM)

        sys.stdout.write("\r" + line + " " * 10)
        sys.stdout.flush()

    def finish(self, final_line):
        self.update(self.total)
        sys.stdout.write("\r" + " " * 120 + "\r")
        print(final_line)

# ===== Utils list files =====
def list_files(root, endswith_tuple):
    for r, _, files in os.walk(root):
        for fn in files:
            if fn.lower().endswith(endswith_tuple):
                yield os.path.join(r, fn)

def count_files(root, endswith_tuple):
    c = 0
    for _ in list_files(root, endswith_tuple):
        c += 1
    return c

# ===== PKCT decode =====
def is_pkct(b: bytes) -> bool:
    return b[:4].lower() == b"pkct" and len(b) > PKCT_HDR

def decode_pkct(data: bytes):
    if not is_pkct(data):
        return None, "bukan_pkct"

    payload = bytearray(data[PKCT_HDR:])

    if len(payload) >= 8 and payload[1:8] == PNG_TAIL:
        payload[0] = 0x89
        return bytes(payload), "png"

    if len(payload) >= 3 and payload[1:3] == JPG_TAIL:
        payload[0] = 0xFF
        return bytes(payload), "jpg"

    return None, "pkct_tapi_pola_tidak_cocok"

def langkah_decode():
    hr("STEP: 1  Membuka PKCT -> step1_decode_raw")
    ensure_dir(ASSETS_ORIGINAL)
    ensure_dir(STEP1_DECODE)

    total = count_files(ASSETS_ORIGINAL, EXTS_IMG)
    bar = ProgressBar(total, "PKCT Decrypt")

    ok = 0
    skip = 0
    skip_bukan = 0
    skip_pola = 0

    i = 0
    for src in list_files(ASSETS_ORIGINAL, EXTS_IMG):
        i += 1
        rel = os.path.relpath(src, ASSETS_ORIGINAL)
        dst = os.path.join(STEP1_DECODE, rel)

        data = open(src, "rb").read()
        out, st = decode_pkct(data)

        if out is None:
            skip += 1
            if st == "bukan_pkct":
                skip_bukan += 1
            else:
                skip_pola += 1
        else:
            ensure_dir(os.path.dirname(dst))
            open(dst, "wb").write(out)
            ok += 1

        bar.update(i, extra=f"ok={ok} skip={skip}")

    bar.finish(color(f"[SELESAI] Decode: OK={ok}  SKIP={skip}", C.BLD + C.GN))
    print()
    print(color("Apa itu SKIP?:", C.YL))
    print()
    print("  - bukan_pkct:", skip_bukan, "(file bukan wrapper PKCT / sudah normal)")
    print("  - pola_tidak_cocok:", skip_pola, "(PKCT tapi bukan PNG/JPG dgn pola yang sesuai metode RyanEx)")
    print("  Output:", STEP1_DECODE)

# ===== PNG repair (soft) =====
def crc32_png(typ: bytes, dat: bytes) -> int:
    return binascii.crc32(typ + dat) & 0xFFFFFFFF

def parse_png_chunks(png_bytes: bytes):
    if not png_bytes.startswith(PNG_SIG):
        return None
    pos = 8
    chunks = []
    n = len(png_bytes)
    while pos + 8 <= n:
        ln = int.from_bytes(png_bytes[pos:pos+4], "big"); pos += 4
        typ = png_bytes[pos:pos+4]; pos += 4
        if pos + ln + 4 > n:
            return None
        dat = png_bytes[pos:pos+ln]; pos += ln
        pos += 4
        chunks.append((typ, dat))
        if typ == b"IEND":
            break
    return chunks

def build_png(chunks):
    out = bytearray(PNG_SIG)
    for typ, dat in chunks:
        out += len(dat).to_bytes(4, "big")
        out += typ
        out += dat
        out += crc32_png(typ, dat).to_bytes(4, "big")
    return bytes(out)

def try_inflate(comp: bytes):
    try:
        return zlib.decompress(comp), "zlib_ok"
    except Exception:
        pass
    try:
        return zlib.decompress(comp, wbits=-15), "raw_ok"
    except Exception:
        pass
    if len(comp) > 6:
        try:
            return zlib.decompress(comp[2:-4], wbits=-15), "strip_hdr_adler_ok"
        except Exception:
            pass
    return None, "hard_protect"

def repair_png(png_bytes: bytes):
    chunks = parse_png_chunks(png_bytes)
    if not chunks:
        return None, "Bukan Image Valid"

    comp = b"".join(dat for (typ, dat) in chunks if typ == b"IDAT")
    if not comp:
        return None, "tidak_ada_idat"

    raw, mode = try_inflate(comp)
    if raw is None:
        return None, mode

    if mode == "zlib_ok":
        return png_bytes, "sudah_normal"

    new_comp = zlib.compress(raw, level=6)
    new_chunks = []
    inserted = False
    for typ, dat in chunks:
        if typ == b"IDAT":
            if not inserted:
                new_chunks.append((b"IDAT", new_comp))
                inserted = True
            continue
        new_chunks.append((typ, dat))
    return build_png(new_chunks), "diperbaiki"

def langkah_fixpng():
    hr("STEP: 2  Membuat Image bisa dibuka -> step2_image_valid")
    ensure_dir(STEP1_DECODE)
    ensure_dir(STEP2_PNG_OK)

    # hitung total image dulu supaya progress bar akurat
    total = count_files(STEP1_DECODE, (".png",))
    bar = ProgressBar(total, "IMAGE Repair")

    fixed = 0
    already = 0
    skip = 0
    hard = 0
    other = 0

    i = 0
    for src in list_files(STEP1_DECODE, (".png",)):
        i += 1
        rel = os.path.relpath(src, STEP1_DECODE)
        dst = os.path.join(STEP2_PNG_OK, rel)

        b = open(src, "rb").read()
        out, st = repair_png(b)

        if out is None:
            skip += 1
            if st == "hard_protect":
                hard += 1
            else:
                other += 1
        else:
            ensure_dir(os.path.dirname(dst))
            open(dst, "wb").write(out)
            if st == "sudah_normal":
                already += 1
            else:
                fixed += 1

        bar.update(i, extra=f"fix={fixed} ok={already} skip={skip}")

    bar.finish(color(f"[SELESAI] FixPNG: DIPERBAIKI={fixed}  SUDAH_NORMAL={already}  SKIP={skip}", C.BLD + C.GN))
    print()
    print(color("Apa itu SKIP?:", C.YL))
    print()
    print("  - hard_protect:", hard, "(IDAT diacak non-trivial -> butuh algoritma dari libgame.so)")
    print("  - lainnya:", other, "(bukan Image valid / chunk rusak)")
    print("  Output:", STEP2_PNG_OK)

# ===== Sheet finder =====
def cari_sheet(png_name: str):
    for root, _, files in os.walk(STEP2_PNG_OK):
        if png_name in files:
            return os.path.join(root, png_name)
    for root, _, files in os.walk(STEP1_DECODE):
        if png_name in files:
            return os.path.join(root, png_name)
    return None

# ===== PLIST extractor =====
def parse_rect_str(s: str):
    s = s.replace("{", "").replace("}", "")
    parts = [p.strip() for p in s.split(",") if p.strip()]
    nums = list(map(int, parts))
    if len(nums) >= 4:
        return nums[0], nums[1], nums[2], nums[3]
    raise ValueError("rect parse gagal")

def extract_plist_one(plist_path: str) -> int:
    if Image is None:
        return 0
    d = plistlib.load(open(plist_path, "rb"))
    meta = d.get("metadata", {})
    frames = d.get("frames", {})
    png_name = meta.get("realTextureFileName") or meta.get("textureFileName")
    if not png_name:
        return 0
    sheet = cari_sheet(png_name)
    if not sheet:
        return 0
    try:
        img = Image.open(sheet); img.load()
    except Exception:
        return 0
    out_dir = os.path.join(EKSTRAK_PLIST, os.path.splitext(os.path.basename(plist_path))[0])
    ensure_dir(out_dir)

    count = 0
    for name, fr in frames.items():
        try:
            if "frame" in fr:
                x, y, w, h = parse_rect_str(fr["frame"])
            elif "textureRect" in fr:
                x, y, w, h = parse_rect_str(fr["textureRect"])
            else:
                continue
            rotated = fr.get("rotated", False)
            crop = img.crop((x, y, x + w, y + h))
            if rotated:
                crop = crop.rotate(90, expand=True)
            out_path = os.path.join(out_dir, name)
            ensure_dir(os.path.dirname(out_path))
            crop.save(out_path)
            count += 1
        except Exception:
            continue
    return count

def langkah_plist():
    hr("STEP: 3  Ekstrak sprite dari .plist -> ekstrak_plist")
    ensure_dir(ASSETS_ORIGINAL)
    ensure_dir(EKSTRAK_PLIST)

    if Image is None:
        print(color("Pillow belum terpasang. Install:", C.RD))
        print("  pkg install -y libjpeg-turbo libpng")
        print("  pip install pillow")
        return

    total = count_files(ASSETS_ORIGINAL, (".plist",))
    bar = ProgressBar(total, "PLIST Extract")

    sprites = 0
    ok = 0
    sk = 0

    i = 0
    for p in list_files(ASSETS_ORIGINAL, (".plist",)):
        i += 1
        n = extract_plist_one(p)
        if n > 0:
            sprites += n
            ok += 1
        else:
            sk += 1
        bar.update(i, extra=f"ok={ok} skip={sk} sprite={sprites}")

    bar.finish(color(f"[SELESAI] PLIST: OK={ok}  SKIP={sk}  SPRITE={sprites}", C.BLD + C.GN))
    print()
    print(color("Apa itu SKIP?:", C.YL))
    print()
    print("  Sheet PNG tidak bisa dibuka (hard protect) atau sheet tidak ada.")
    print("  Output:", EKSTRAK_PLIST)

# ===== ATLAS extractor =====
def parse_atlas(atlas_path: str):
    with open(atlas_path, "r", encoding="utf-8", errors="ignore") as f:
        lines = [l.rstrip("\n") for l in f]
    sheet = None
    regions = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if sheet is None and line.lower().endswith(".png"):
            sheet = line
            i += 1
            continue
        if line and (":" not in line) and not line.lower().endswith(".png"):
            name = line
            xy = None
            size = None
            rotate = False
            i += 1
            while i < len(lines) and ":" in lines[i]:
                k, v = lines[i].split(":", 1)
                k = k.strip(); v = v.strip()
                if k == "xy":
                    xy = tuple(int(x.strip()) for x in v.split(","))
                elif k == "size":
                    size = tuple(int(x.strip()) for x in v.split(","))
                elif k == "rotate":
                    rotate = (v.lower() == "true")
                i += 1
            if sheet and xy and size:
                x, y = xy; w, h = size
                regions.append((name, x, y, w, h, rotate))
            continue
        i += 1
    return sheet, regions

def langkah_atlas():
    hr("STEP: 4  Ekstrak sprite dari .atlas -> ekstrak_atlas")
    ensure_dir(ASSETS_ORIGINAL)
    ensure_dir(EKSTRAK_ATLAS)

    if Image is None:
        print(color("Pillow belum terpasang. Install:", C.RD))
        print("  pkg install -y libjpeg-turbo libpng")
        print("  pip install pillow")
        return

    total = count_files(ASSETS_ORIGINAL, (".atlas",))
    bar = ProgressBar(total, "ATLAS Extract")

    ok = 0
    sk = 0
    regions_out = 0

    i = 0
    for atlas_path in list_files(ASSETS_ORIGINAL, (".atlas",)):
        i += 1
        sheet_name, regions = parse_atlas(atlas_path)
        if not sheet_name or not regions:
            sk += 1
            bar.update(i, extra=f"ok={ok} skip={sk} region={regions_out}")
            continue

        sheet_path = cari_sheet(sheet_name)
        if not sheet_path:
            sk += 1
            bar.update(i, extra=f"ok={ok} skip={sk} region={regions_out}")
            continue

        try:
            img = Image.open(sheet_path); img.load()
        except Exception:
            sk += 1
            bar.update(i, extra=f"ok={ok} skip={sk} region={regions_out}")
            continue

        out_dir = os.path.join(EKSTRAK_ATLAS, os.path.splitext(os.path.basename(atlas_path))[0])
        ensure_dir(out_dir)

        count = 0
        for name, x, y, w, h, rot in regions:
            try:
                crop = img.crop((x, y, x + w, y + h))
                if rot:
                    crop = crop.rotate(90, expand=True)
                crop.save(os.path.join(out_dir, name + ".png"))
                count += 1
            except Exception:
                continue

        if count > 0:
            ok += 1
            regions_out += count
        else:
            sk += 1

        bar.update(i, extra=f"ok={ok} skip={sk} region={regions_out}")

    bar.finish(color(f"[SELESAI] ATLAS: OK={ok}  SKIP={sk}  REGION={regions_out}", C.BLD + C.GN))
    print()
    print(color("Apa itu SKIP?:", C.YL))
    print()
    print("  Sheet PNG tidak bisa dibuka (hard protect) atau format atlas berbeda.")
    print("  Output:", EKSTRAK_ATLAS)

def ringkasan():
    hr("RINGKASAN FOLDER HASIL")
    print(color("Input Assets Raw:", C.BL), ASSETS_ORIGINAL)
    print(color("Step 1 Decode Raw:", C.BL), STEP1_DECODE)
    print(color("Step 2 Image Valid:", C.BL), STEP2_PNG_OK)
    print(color("Plist Extract:", C.BL), EKSTRAK_PLIST)
    print(color("Atlas Extract:", C.BL), EKSTRAK_ATLAS)
    print(color("Catatan:", C.YL))
    print("  - Step 1 = sudah buka PKCT, tapi PNG masih Hard Protect.")
    print("  - Step 2 = hanya PNG yang bisa dinormalisasi.")
    print("  - SKIP bukan error fatal, itu kategori file yang tidak bisa diproses oleh metode RyanEx.")

def usage():
    print("Perintah:")
    print("  python image_decrypter_v4.py            -> default: all")
    print("  python image_decrypter_v4.py decode     -> PKCT -> step1_decode_raw")
    print("  python image_decrypter_v4.py fix_image     -> perbaiki PNG -> step2_image_valid")
    print("  python image_decrypter_v4.py plist      -> ekstrak sprite plist")
    print("  python image_decrypter_v4.py atlas      -> ekstrak sprite atlas")
    print("  python image_decrypter_v4.py all        -> semua step")

def show_menu():
    while True:
        print()
        print(color(" ┌─ MAIN MENU ─┐", C.BLD + "\033[38;5;75m"))
        print()
        print(color("1]", C.YL), "PKCT Decrypt")
        print(color("2]", C.YL), "Image Repair")
        print(color("3]", C.YL), "Plist Extract")
        print(color("4]", C.YL), "Atlas Extract")
        print(color("5]", C.YL), "All")
        print()

        pilihan = input(color("Pilih Nomor (Enter): ", C.GY)).strip()

        if pilihan in ("1", "2", "3", "4", "5"):
            return pilihan

        print()
        print(color("Pilihan tidak valid. Ketik nomor 1-5 lalu tekan Enter!", C.RD))
        time.sleep(2.0)
        os.system("clear")
        show_title()

def main():
    os.system("clear")
    show_title()

    ensure_dir(ASSETS_ORIGINAL)
    ensure_dir(HASIL_ROOT)
    ensure_dir(STEP1_DECODE)
    ensure_dir(STEP2_PNG_OK)
    ensure_dir(EKSTRAK_PLIST)
    ensure_dir(EKSTRAK_ATLAS)

    try:
        # ===== MODE MENU (tanpa argumen) =====
        if len(sys.argv) == 1:

            while True:
                cmd = show_menu()
                # Jika kosong → ulang menu
                os.system("clear")
                show_title()

                if cmd == "1":
                    langkah_decode()
                elif cmd == "2":
                    langkah_fixpng()
                elif cmd == "3":
                    langkah_plist()
                elif cmd == "4":
                    langkah_atlas()
                elif cmd == "5":
                    langkah_decode()
                    langkah_fixpng()
                    langkah_plist()
                    langkah_atlas()
                    ringkasan()

                input(color("\nTekan Enter untuk kembali ke menu...", C.GY))
                os.system("clear")
                show_title()

        # ===== MODE ARGUMENT CLI =====
        else:
            cmd = sys.argv[1].lower().strip()

            if cmd == "decode":
                langkah_decode()
            elif cmd == "fix_image":
                langkah_fixpng()
            elif cmd == "plist":
                langkah_plist()
            elif cmd == "atlas":
                langkah_atlas()
            elif cmd == "all":
                langkah_decode()
                langkah_fixpng()
                langkah_plist()
                langkah_atlas()
                ringkasan()
            else:
                usage()
    finally:
        print()
        show_footer()
        
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass