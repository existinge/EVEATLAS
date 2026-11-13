// ExportFunctions.java — Ghidra headless export for the Note9-SD845 diff pipeline.
//
// Runs inside analyzeHeadless as:
//   ghidra -analyzeHeadless <proj> <name> -import <bin> \
//     -postScript ExportFunctions.java <out-json> <rev-tag>
//
// Writes the JSON contract described in docs/02-ghidra-bindiff-pipeline.md §2 Stage B:
// per-function name, addr, size, mnemonic histogram, referenced constants,
// called-function names, and block count. String-safe for the downstream aligner.

import java.io.File;
import java.io.FileWriter;
import java.nio.file.Files;
import java.io.PrintWriter;
import java.util.*;

import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.*;
import ghidra.program.model.address.*;
import ghidra.program.model.symbol.*;
import ghidra.program.model.mem.*;

public class ExportFunctions extends GhidraScript {

    @Override
    public void run() throws Exception {
        if (getScriptArgs().length < 1) {
            println("usage: -postScript ExportFunctions.java <out-json> [rev-tag]");
            return;
        }
        String outPath = getScriptArgs()[0];
        String revTag  = getScriptArgs().length > 1 ? getScriptArgs()[1]
                                                     : getProgram().getName();

        Listing listing = currentProgram.getListing();
        FunctionManager fm = currentProgram.getFunctionManager();
        ReferenceManager rm = currentProgram.getReferenceManager();

        StringBuilder sb = new StringBuilder();
        sb.append("{\n  \"image\": {\n");
        sb.append("    \"file\": \"" + esc(currentProgram.getExecutablePath()) + "\",\n");
        sb.append("    \"name\": \"" + esc(currentProgram.getName()) + "\",\n");
        sb.append("    \"rev\": \"" + esc(revTag) + "\",\n");
        sb.append("    \"base\": " + currentProgram.getImageBase().getOffset() + ",\n");
        sb.append("    \"language\": \"" + esc(currentProgram.getLanguageID().getIdAsString()) + "\"\n");
        sb.append("  },\n  \"functions\": [\n");

        boolean first = true;
        for (Function f : fm.getFunctions(true)) {
            String name = f.getName();
            long addr = f.getEntryPoint().getOffset();
            long size = f.getBody().getNumAddresses();

            // mnemonic histogram over the function body
            Map<String, Integer> mn = new TreeMap<>();
            AddressIterator it = currentProgram.getAddressFactory().getAddressSetIterator(f.getBody());
            while (it.hasNext()) {
                Address a = it.next();
                Instruction ins = listing.getInstructionAt(a);
                if (ins != null) {
                    String m = ins.getMnemonic();
                    mn.merge(m, 1, Integer::sum);
                }
            }

            // direct called callees
            Set<String> callees = new TreeSet<>();
            for (Reference r : rm.getReferencesTo(f.getEntryPoint())) {
                if (r.getReferenceType().isCall()) {
                    Address from = r.getFromAddress();
                    Function cf = fm.getFunctionContaining(from);
                    if (cf != null) callees.add(cf.getName());
                }
            }

            if (!first) sb.append(",\n");
            first = false;

            sb.append("    {\"name\":\"" + esc(name) + "\",\"addr\":" + addr
                    + ",\"size\":" + size
                    + ",\"blocks\":" + f.getBody().getNumAddresses()
                    + ",\"mnemonics\":{");
            boolean fmn = true;
            for (Map.Entry<String, Integer> e : mn.entrySet()) {
                if (!fmn) sb.append(",");
                fmn = false;
                sb.append("\"" + esc(e.getKey()) + "\":" + e.getValue());
            }
            sb.append("},\"calls\":[");
            boolean fc = true;
            for (String c : callees) {
                if (!fc) sb.append(",");
                fc = false;
                sb.append("\"" + esc(c) + "\"");
            }
            sb.append("] }");
        }
        sb.append("\n  ]\n}\n");

        File fout = new File(outPath);
        fout.getParentFile().mkdirs();
        try (PrintWriter w = new PrintWriter(new FileWriter(fout))) {
            w.write(sb.toString());
        }
        println("ExportFunctions: wrote " + fout.getAbsolutePath());
    }

    private static String esc(String s) {
        return s.replace("\\", "\\\\").replace("\"", "\\\"");
    }
}