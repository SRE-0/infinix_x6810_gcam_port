import brut.androlib.smali.SmaliBuilder;
import com.android.tools.smali.dexlib2.Opcodes;
import com.android.tools.smali.dexlib2.writer.builder.DexBuilder;
import com.android.tools.smali.dexlib2.writer.io.FileDataStore;
import java.nio.file.*;

/** Assemble one isolated DEX directory using the already installed apktool. */
class AssembleSmali {
    public static void main(String[] args) throws Exception {
        // DEX 039 uses the classic 112-byte header. The installed apktool's
        // API-35 writer emits a 041 magic with an incompatible classic header.
        DexBuilder dex = new DexBuilder(new Opcodes(28));
        SmaliBuilder assembler = new SmaliBuilder(28);
        var files = Files.walk(Path.of(args[0])).filter(p -> p.toString().endsWith(".smali"))
            .sorted().toList();
        int count = 0;
        for (Path file : files) {
            if (!assembler.buildFile(file.toFile(), dex)) throw new Exception("Invalid smali: " + file);
            if (++count % 1000 == 0) System.out.println("Assembled " + count + "/" + files.size());
        }
        dex.writeTo(new FileDataStore(Path.of(args[1]).toFile()));
        System.out.println("Wrote " + args[1] + " (" + count + " classes)");
    }
}
