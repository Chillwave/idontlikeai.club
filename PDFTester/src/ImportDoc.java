import org.apache.pdfbox.Loader;
import org.apache.pdfbox.pdmodel.PDDocument;
import org.apache.pdfbox.text.PDFTextStripper;

import java.io.File;
import java.io.IOException;

public class ImportDoc {
    private String filePath;

    public ImportDoc(String filePath){
        this.filePath = filePath;
    }

    public String getContents() throws IOException {
        File file = new File(this.filePath);
        PDDocument document = Loader.loadPDF(file);
        PDFTextStripper stripper = new PDFTextStripper();
        return stripper.getText(document);
    }

    public void printEncoded(String text){
        String result = "";
        for(int i = 0; i < text.length(); i++){
            if(Character.isLetterOrDigit(text.charAt(i))){
                result += (char) (((int)text.charAt(i)%65) + 68);
            }
            else{
                result += text.charAt(i);
            }

        }

        System.out.println(result);
    }
}
