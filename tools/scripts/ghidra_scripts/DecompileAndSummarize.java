// Ghidra Headless Post-Script: Decompile functions and output summary & C pseudocode
//@category Analysis
//@author Antigravity

import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.decompiler.DecompiledFunction;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.FunctionIterator;
import ghidra.program.model.listing.Program;
import ghidra.program.model.mem.MemoryBlock;

import java.io.File;
import java.io.FileWriter;
import java.io.PrintWriter;
import java.util.Date;

public class DecompileAndSummarize extends GhidraScript {

    @Override
    public void run() throws Exception {
        String[] args = getScriptArgs();
        String outputDir = null;
        if (args.length > 0 && args[0] != null && !args[0].trim().isEmpty()) {
            outputDir = args[0].trim();
        }

        Program prog = currentProgram;
        if (prog == null) {
            println("[-] No program loaded for decompilation.");
            return;
        }

        String progName = prog.getName();
        println("=================================================");
        println("[+] Ghidra Headless Analysis: " + progName);
        println("[+] Architecture: " + prog.getLanguage().getProcessor().toString() + " (" + prog.getAddressFactory().getDefaultAddressSpace().getSize() + "-bit)");
        println("[+] Executable Format: " + prog.getExecutableFormat());
        println("[+] Base Address: " + prog.getImageBase());
        println("=================================================");

        File cOutputFile = null;
        File summaryOutputFile = null;
        PrintWriter cWriter = null;
        PrintWriter summaryWriter = null;

        if (outputDir != null) {
            File dir = new File(outputDir);
            if (!dir.exists()) {
                dir.mkdirs();
            }
            cOutputFile = new File(dir, progName + ".decompiled.c");
            summaryOutputFile = new File(dir, progName + ".summary.txt");
            cWriter = new PrintWriter(new FileWriter(cOutputFile));
            summaryWriter = new PrintWriter(new FileWriter(summaryOutputFile));

            summaryWriter.println("GHIDRA HEADLESS ANALYSIS SUMMARY");
            summaryWriter.println("Date: " + new Date());
            summaryWriter.println("Target: " + progName);
            summaryWriter.println("Format: " + prog.getExecutableFormat());
            summaryWriter.println("Language: " + prog.getLanguageID());
            summaryWriter.println("Compiler Spec: " + prog.getCompilerSpec().getCompilerSpecID());
            summaryWriter.println("Image Base: " + prog.getImageBase());
            summaryWriter.println("\nMemory Blocks:");
            for (MemoryBlock block : prog.getMemory().getBlocks()) {
                summaryWriter.println(String.format("  %-20s %016x - %016x (Size: 0x%x, R:%b, W:%b, X:%b)",
                    block.getName(),
                    block.getStart().getOffset(),
                    block.getEnd().getOffset(),
                    block.getSize(),
                    block.isRead(),
                    block.isWrite(),
                    block.isExecute()));
            }
            summaryWriter.println("\nFUNCTIONS & DECOMPILATION SUMMARY:");
        }

        DecompInterface decompiler = new DecompInterface();
        decompiler.openProgram(prog);

        FunctionIterator functions = prog.getFunctionManager().getFunctions(true);
        int totalFuncs = 0;
        int decompiledCount = 0;
        int errorCount = 0;

        if (cWriter != null) {
            cWriter.println("// Decompiled by Ghidra Headless Analyzer");
            cWriter.println("// Program: " + progName);
            cWriter.println("// Timestamp: " + new Date());
            cWriter.println();
        }

        println(String.format("%-20s %-35s %-15s", "Address", "Function Name", "Decompile Status"));
        println("--------------------------------------------------------------------------------");

        while (functions.hasNext() && !monitor.isCancelled()) {
            Function func = functions.next();
            totalFuncs++;
            String funcName = func.getName();
            String funcAddr = func.getEntryPoint().toString();

            DecompileResults results = decompiler.decompileFunction(func, 30, monitor);
            if (results != null && results.decompileCompleted()) {
                decompiledCount++;
                DecompiledFunction decompFunc = results.getDecompiledFunction();
                String cCode = (decompFunc != null) ? decompFunc.getC() : "// [No C code produced]";
                
                println(String.format("0x%-18s %-35s [SUCCESS]", funcAddr, funcName));
                if (summaryWriter != null) {
                    summaryWriter.println(String.format("0x%-18s %-35s [SUCCESS] (Size: %d bytes)", funcAddr, funcName, func.getBody().getNumAddresses()));
                }
                if (cWriter != null) {
                    cWriter.println("/*");
                    cWriter.println(" * Function: " + funcName);
                    cWriter.println(" * Address:  0x" + funcAddr);
                    cWriter.println(" * Signature: " + func.getPrototypeString(true, false));
                    cWriter.println(" */");
                    cWriter.println(cCode);
                    cWriter.println();
                }
            } else {
                errorCount++;
                String err = (results != null) ? results.getErrorMessage() : "Unknown error";
                println(String.format("0x%-18s %-35s [FAILED: %s]", funcAddr, funcName, err));
                if (summaryWriter != null) {
                    summaryWriter.println(String.format("0x%-18s %-35s [FAILED: %s]", funcAddr, funcName, err));
                }
                if (cWriter != null) {
                    cWriter.println("// FAILED to decompile " + funcName + " @ 0x" + funcAddr + ": " + err);
                }
            }
        }

        decompiler.dispose();

        println("--------------------------------------------------------------------------------");
        println(String.format("[+] Total Functions: %d | Decompiled: %d | Errors: %d", totalFuncs, decompiledCount, errorCount));

        if (summaryWriter != null) {
            summaryWriter.println("\nTOTAL STATISTICS:");
            summaryWriter.println("  Total Functions: " + totalFuncs);
            summaryWriter.println("  Successfully Decompiled: " + decompiledCount);
            summaryWriter.println("  Failed: " + errorCount);
            summaryWriter.flush();
            summaryWriter.close();
            println("[+] Summary written to: " + summaryOutputFile.getAbsolutePath());
        }

        if (cWriter != null) {
            cWriter.flush();
            cWriter.close();
            println("[+] Decompiled C code written to: " + cOutputFile.getAbsolutePath());
        }
        println("=================================================");
    }
}
