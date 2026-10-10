// Ghidra headless script for the wc1 decompilation (decompiler HINTS only).
//
// Input (from wc1.ghidra_decomp prepare): a directory with meta.txt, code.bin and
// data.bin. The program is imported by analyzeHeadless as a raw binary; this script
//   1. replaces the memory with two blocks: "code" at 0x10000 (r-x) and "data" at
//      0x50000 (rw-), taken from the loaded objects (fixups already applied);
//   2. adds a "__watcall" prototype (Watcom register convention, which Ghidra lacks),
//      creates a function at every start listed in meta.txt with that convention, names
//      it, and creates labels for data symbols and 4-byte pointer data at fixup sites in
//      the data object;
//   3. runs Ghidra auto-analysis;
//   4. decompiles every listed function (60 s timeout each) into
//      <output dir>/<start:05x>_<name>.c and writes <output dir>/index.tsv.
//
// Usage: analyzeHeadless ... -postScript WcDecomp.java <input dir> <output dir>

import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.database.SpecExtension;
import ghidra.program.model.address.Address;
import ghidra.program.model.address.AddressSpace;
import ghidra.program.model.data.Pointer32DataType;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.Program;
import ghidra.program.model.mem.Memory;
import ghidra.program.model.mem.MemoryBlock;
import ghidra.program.model.symbol.RefType;
import ghidra.program.model.symbol.SourceType;

import java.io.File;
import java.io.FileInputStream;
import java.io.InputStream;
import java.io.PrintWriter;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.List;

public class WcDecomp extends GhidraScript {

    private static final int TIMEOUT_SECS = 60;
    private static final String WATCALL = "__watcall";
    // Watcom register calling convention: eax, edx, ebx, ecx, then the stack
    // (removed by the callee); result in eax (edx:eax for 8 bytes); every other
    // register is preserved by the callee.
    private static final String WATCALL_XML =
        "<prototype name=\"" + WATCALL + "\" extrapop=\"unknown\" stackshift=\"4\">"
        + "<input>"
        + "<pentry minsize=\"1\" maxsize=\"4\"><register name=\"EAX\"/></pentry>"
        + "<pentry minsize=\"1\" maxsize=\"4\"><register name=\"EDX\"/></pentry>"
        + "<pentry minsize=\"1\" maxsize=\"4\"><register name=\"EBX\"/></pentry>"
        + "<pentry minsize=\"1\" maxsize=\"4\"><register name=\"ECX\"/></pentry>"
        + "<pentry minsize=\"1\" maxsize=\"500\" align=\"4\"><addr offset=\"4\" space=\"stack\"/></pentry>"
        + "</input>"
        + "<output>"
        + "<pentry minsize=\"1\" maxsize=\"4\"><register name=\"EAX\"/></pentry>"
        + "<pentry minsize=\"5\" maxsize=\"8\"><addr space=\"join\" piece1=\"EDX\" piece2=\"EAX\"/></pentry>"
        + "</output>"
        + "<unaffected>"
        + "<register name=\"EBX\"/><register name=\"ECX\"/><register name=\"EDX\"/>"
        + "<register name=\"ESI\"/><register name=\"EDI\"/><register name=\"EBP\"/>"
        + "<register name=\"ESP\"/><register name=\"DF\"/>"
        + "</unaffected>"
        + "</prototype>";

    private static final class Func {
        long start, end;
        String name;
    }

    private static final class Sym {
        long addr;
        String name;
    }

    private static final class Fix {
        long site, target;
        int size;
    }

    @Override
    protected void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length != 2) {
            throw new IllegalArgumentException("usage: WcDecomp.java <input dir> <output dir>");
        }
        File inDir = new File(args[0]);
        Path outDir = Paths.get(args[1]);

        long codeBase = 0, codeSize = 0, dataBase = 0, dataSize = 0;
        String codeFile = null, dataFile = null;
        List<Func> funcs = new ArrayList<>();
        List<Sym> syms = new ArrayList<>();
        List<Fix> fixes = new ArrayList<>();
        for (String line : Files.readAllLines(new File(inDir, "meta.txt").toPath(),
                StandardCharsets.UTF_8)) {
            if (line.isEmpty() || line.startsWith("#")) {
                continue;
            }
            String[] f = line.split(" ");
            switch (f[0]) {
                case "CODE":
                    codeBase = Long.parseLong(f[1], 16);
                    codeSize = Long.parseLong(f[2], 16);
                    codeFile = f[3];
                    break;
                case "DATA":
                    dataBase = Long.parseLong(f[1], 16);
                    dataSize = Long.parseLong(f[2], 16);
                    dataFile = f[3];
                    break;
                case "F": {
                    Func fn = new Func();
                    fn.start = Long.parseLong(f[1], 16);
                    fn.end = Long.parseLong(f[2], 16);
                    fn.name = f[3];
                    funcs.add(fn);
                    break;
                }
                case "D": {
                    Sym s = new Sym();
                    s.addr = Long.parseLong(f[1], 16);
                    s.name = f[2];
                    syms.add(s);
                    break;
                }
                case "P": {
                    Fix x = new Fix();
                    x.site = Long.parseLong(f[1], 16);
                    x.target = Long.parseLong(f[2], 16);
                    x.size = Integer.parseInt(f[3]);
                    fixes.add(x);
                    break;
                }
                default:
                    throw new IllegalArgumentException("bad meta line: " + line);
            }
        }
        println("meta: " + funcs.size() + " functions, " + syms.size() + " data symbols, "
                + fixes.size() + " fixups");

        Program prog = currentProgram;
        AddressSpace space = prog.getAddressFactory().getDefaultAddressSpace();
        Memory mem = prog.getMemory();

        // 1. Memory layout from the loaded objects.
        int tx = prog.startTransaction("wc1 memory");
        try {
            for (MemoryBlock b : mem.getBlocks()) {
                mem.removeBlock(b, monitor);
            }
            try (InputStream in = new FileInputStream(new File(inDir, codeFile))) {
                MemoryBlock code = mem.createInitializedBlock("code", space.getAddress(codeBase),
                        in, codeSize, monitor, false);
                code.setRead(true);
                code.setWrite(false);
                code.setExecute(true);
            }
            try (InputStream in = new FileInputStream(new File(inDir, dataFile))) {
                MemoryBlock data = mem.createInitializedBlock("data", space.getAddress(dataBase),
                        in, dataSize, monitor, false);
                data.setRead(true);
                data.setWrite(true);
                data.setExecute(false);
            }
            prog.endTransaction(tx, true);
        } catch (Exception e) {
            prog.endTransaction(tx, false);
            throw e;
        }

        // 2. Functions (Watcom convention), labels and pointer data.
        new SpecExtension(prog).addReplaceCompilerSpecExtension(WATCALL_XML, monitor);
        int skippedFuncs = 0, skippedPtr = 0;
        tx = prog.startTransaction("wc1 functions");
        try {
            for (Func fn : funcs) {
                Address a = space.getAddress(fn.start);
                try {
                    disassemble(a);
                    Function f = getFunctionAt(a);
                    if (f == null) {
                        f = createFunction(a, fn.name);
                    }
                    if (f == null) {
                        skippedFuncs++;
                        printerr("no function at " + a);
                    } else {
                        if (!f.getName().equals(fn.name)) {
                            f.setName(fn.name, SourceType.USER_DEFINED);
                        }
                        f.setCallingConvention(WATCALL);
                    }
                } catch (Exception e) {
                    skippedFuncs++;
                    printerr("function " + a + " " + fn.name + ": " + e);
                }
            }
            for (Sym s : syms) {
                try {
                    Address a = space.getAddress(s.addr);
                    createLabel(a, s.name, true);
                } catch (Exception e) {
                    printerr("label " + s.name + ": " + e);
                }
            }
            for (Fix x : fixes) {
                // Only 4-byte absolute pointers in the data object are typed here.
                if (x.size != 4 || x.site < dataBase || x.site >= dataBase + dataSize) {
                    continue;
                }
                try {
                    Address site = space.getAddress(x.site);
                    Address target = space.getAddress(x.target);
                    createData(site, Pointer32DataType.dataType);
                    prog.getReferenceManager().addMemoryReference(site, target, RefType.DATA,
                            SourceType.ANALYSIS, 0);
                } catch (Exception e) {
                    skippedPtr++;
                }
            }
            prog.endTransaction(tx, true);
        } catch (Exception e) {
            prog.endTransaction(tx, false);
            throw e;
        }
        println("setup: functions skipped " + skippedFuncs + ", pointer sites skipped "
                + skippedPtr);

        // 3. Auto-analysis.
        println("auto-analysis ...");
        analyzeAll(prog);

        // Analysis may rename functions; restore the DB names.
        tx = prog.startTransaction("wc1 names");
        try {
            for (Func fn : funcs) {
                Function f = getFunctionAt(space.getAddress(fn.start));
                if (f != null && !f.getName().equals(fn.name)) {
                    try {
                        f.setName(fn.name, SourceType.USER_DEFINED);
                    } catch (Exception e) {
                        printerr("rename " + fn.name + ": " + e);
                    }
                }
            }
            prog.endTransaction(tx, true);
        } catch (Exception e) {
            prog.endTransaction(tx, false);
            throw e;
        }

        // 4. Decompile every function.
        Files.createDirectories(outDir);
        for (File old : outDir.toFile().listFiles()) {
            if (old.getName().endsWith(".c") || old.getName().equals("index.tsv")
                    || old.getName().equals("errors.txt")) {
                old.delete();
            }
        }

        DecompInterface ifc = new DecompInterface();
        ifc.toggleCCode(true);
        ifc.openProgram(prog);
        int ok = 0, timeout = 0, error = 0;
        try (PrintWriter index = new PrintWriter(outDir.resolve("index.tsv").toFile(),
                "UTF-8");
             PrintWriter errs = new PrintWriter(outDir.resolve("errors.txt").toFile(),
                     "UTF-8")) {
            index.println("start\tend\tname\tstatus");
            int n = 0;
            for (Func fn : funcs) {
                if (monitor.isCancelled()) {
                    break;
                }
                n++;
                if (n % 100 == 0) {
                    println("decompiled " + n + "/" + funcs.size());
                }
                String status;
                Function f = getFunctionAt(space.getAddress(fn.start));
                if (f == null) {
                    status = "error";
                    errs.println(hex5(fn.start) + " no function");
                } else {
                    DecompileResults res = ifc.decompileFunction(f, TIMEOUT_SECS, monitor);
                    if (res.isTimedOut()) {
                        status = "timeout";
                        errs.println(hex5(fn.start) + " timeout after " + TIMEOUT_SECS + " s");
                    } else if (res.decompileCompleted() && res.getDecompiledFunction() != null) {
                        status = "ok";
                        Path out = outDir.resolve(hex5(fn.start) + "_" + safeName(fn.name) + ".c");
                        try (PrintWriter w = new PrintWriter(out.toFile(), "UTF-8")) {
                            w.println("/* Ghidra decompiler hint for war.exe function "
                                    + hex5(fn.start) + " (" + fn.name + "). */");
                            w.println("/* Generated by tools/ghidra/WcDecomp.java. A hint, never evidence. */");
                            w.print(res.getDecompiledFunction().getC());
                        }
                    } else {
                        status = "error";
                        errs.println(hex5(fn.start) + " " + fn.name + ": "
                                + res.getErrorMessage());
                    }
                }
                if (status.equals("ok")) {
                    ok++;
                } else if (status.equals("timeout")) {
                    timeout++;
                } else {
                    error++;
                }
                index.println(hex5(fn.start) + "\t" + hex5(fn.end) + "\t" + fn.name + "\t" + status);
            }
        }
        ifc.dispose();
        println("decompile: ok " + ok + ", timeout " + timeout + ", error " + error);
    }

    private static String hex5(long a) {
        return String.format("%05x", a);
    }

    private static String safeName(String s) {
        return s.replaceAll("[^A-Za-z0-9_]", "_");
    }
}
