"""Run war.exe's own archive code (T4 harness) on a DATA.WAR image.

The original functions are executed under wc1.emu; only the C-library
primitives they sit on are replaced by Python models of a stdio FILE over the
archive bytes:

    0x31a80  fseek(FILE, off, whence)       (eax, edx, ebx)
    0x31adc  fread(buf, size, n, FILE)      (eax, edx, ebx, ecx)
    0x31a18  fill/getc slow path (FILE)     (eax) -> next byte or -1
    0x32558  malloc(n)      0x32780 free    0x342b0 atexit
    0x30bf0  fatal error printf -> EmuError

Everything else is original code: OpenArchive 0x34480 (version check, count,
offset table), ResourceSeek 0x3452c, ResourceBegin 0x31870 (header + codec
dispatch), ResourceRead 0x32740, the LZSS decoder 0x41550 + reset 0x417cc and
the stored-copy decoder 0x409a0.
"""
import struct

from .emu import Emu, EmuError

OPEN_ARCHIVE = 0x34480      # fn_34480(FILE*)
SEEK_ENTRY = 0x3452c        # fn_3452c(resource_id) -> file bytes up to next entry
RES_BEGIN = 0x31870         # fn_31870(resource_id, u32 *compressed_len) -> unpacked size
RES_READ = 0x32740          # fn_32740(dest|0, size|0) -> dest
LZSS_DECODE = 0x41550       # fn_41550(dest, n)
LZSS_RESET = 0x417cc        # fn_417cc()
CODEC_TABLE = 0x56524       # 17-byte descriptors indexed by codec id
LZSS_DESC = 0x565d0         # static descriptor of codec 1
FILE_PTR = 0x5581c
RING_PTR = 0x5677c
REMAIN = 0x5ad40
CODEC_ID = 0x5ad44


class ArchiveEmu:
    def __init__(self, data, getc_inline=False):
        """`data`: the DATA.WAR bytes. getc_inline=True gives the FILE a
        full read buffer with the binary flag so the decoder's inlined getc
        fast path (no call to 0x31a18) is exercised too."""
        self.data = bytes(data)
        self.pos = 0
        self.errors = []
        e = self.emu = Emu(max_insns=2_000_000_000)
        self.file = e.alloc(0x40)
        self.getc_inline = getc_inline
        st = e.stubs
        st[0x31a80] = self._fseek
        st[0x31adc] = self._fread
        st[0x31a18] = self._fill
        st[0x32558] = lambda em: em.alloc(em.reg("eax"))
        st[0x32780] = lambda em: 0
        st[0x342b0] = lambda em: 0
        st[0x30bf0] = self._fatal
        e.stub_pops[0x30bf0] = 0
        # register codec 1 the way fn_3b980 does (17-byte descriptor copy)
        desc = e.read(LZSS_DESC, 17)
        e.write(CODEC_TABLE + 17 * desc[0], desc)
        ring = e.alloc(0x1000)
        e.put_u32(RING_PTR, ring)
        e.put_u32(0x62890, 0x56F38)       # main() 0x1e168: version-mismatch message
        e.put_u32(0x55824, 0x18)          # expected version, stored by main() at 0x1e15e
        self._sync_file()

    # -- FILE model -------------------------------------------------------
    WINDOW = 0x1000

    def _sync_file(self):
        e = self.emu
        if self.getc_inline:
            if not hasattr(self, "_win"):
                self._win = e.alloc(self.WINDOW)
            chunk = self.data[self.pos:self.pos + self.WINDOW]
            e.write(self._win, chunk)
            self._wstart = self.pos
            e.put_u32(self.file, self._win)
            e.put_u32(self.file + 4, len(chunk))
            e.put_u32(self.file + 0xC, 4)       # binary: no CR/^Z handling
        else:
            e.put_u32(self.file, 0)
            e.put_u32(self.file + 4, 0)         # empty buffer -> slow path
            e.put_u32(self.file + 0xC, 0)

    def _cur(self):
        """Position as seen by the FILE (accounting for the inline buffer)."""
        if self.getc_inline:
            return self._wstart + (self.emu.u32(self.file) - self._win)
        return self.pos

    def _fseek(self, em):
        assert em.reg("ebx") == 0, "only SEEK_SET is modelled"
        self.pos = em.reg("edx")
        self._sync_file()
        return 0

    def _fread(self, em):
        buf, size, n = em.reg("eax"), em.reg("edx"), em.reg("ebx")
        self.pos = self._cur()
        want = size * n
        chunk = self.data[self.pos:self.pos + want]
        em.write(buf, chunk)
        self.pos += len(chunk)
        self._sync_file()
        return len(chunk) // size

    def _fill(self, em):
        self.pos = self._cur()
        if self.pos >= len(self.data):
            return 0xFFFFFFFF
        c = self.data[self.pos]
        self.pos += 1
        self._sync_file()
        return c

    def _fatal(self, em):
        fmt = b""
        try:
            fmt = em.cstr(em.u32(em.reg("esp") + 4))
        except Exception:
            pass
        self.errors.append(fmt)
        em._error = EmuError(f"war.exe fatal error: {fmt!r}")
        em.uc.emu_stop()
        return 0

    # -- high level -------------------------------------------------------
    def open(self):
        self.pos = 0
        self._sync_file()
        self.emu.call(OPEN_ARCHIVE, self.file)
        return self.emu.u32(0x62894)            # entry count read by fn_34480

    def read_resource(self, rid, chunks=None):
        """Original-code path for resource id `rid`: returns (data, packed_len,
        codec). `chunks`: optional iterable of piece sizes for the decode
        calls (state must survive across calls)."""
        e = self.emu
        heap = e._heap                  # scratch buffers are released on return
        try:
            return self._read_resource(rid, chunks)
        finally:
            e._heap = heap

    def _read_resource(self, rid, chunks):
        e = self.emu
        lenp = e.alloc(4)
        size = e.call(RES_BEGIN, rid, lenp)
        packed = e.u32(lenp)
        codec = e.read(CODEC_ID, 1)[0]
        dest = e.alloc(size + 16)
        if chunks is None:
            e.call(RES_READ, dest, size)
        else:
            done = 0
            for c in chunks:
                c = min(c, size - done)
                if c <= 0:
                    break
                e.call(LZSS_DECODE if codec == 1 else 0x409a0, dest + done, c)
                done += c
            if done < size:
                e.call(LZSS_DECODE if codec == 1 else 0x409a0, dest + done, size - done)
        return e.read(dest, size), packed, codec
