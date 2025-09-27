import org.apache.pdfbox.Loader;
import org.apache.pdfbox.pdmodel.PDDocument;
import org.apache.pdfbox.text.PDFTextStripper;

import java.io.*;

public class ImportDoc {
    // private fields hold filePath text for use through class
    private String filePath;

    // one-arg constructor to construct object and set filePath name
    public ImportDoc(String filePath){
        this.filePath = filePath;
    }

    public String getContents() throws IOException{
        File file = new File(this.filePath);
        PDDocument document = Loader.loadPDF(file);
        PDFTextStripper stripper = new PDFTextStripper();
        return stripper.getText(document);
    }

}
