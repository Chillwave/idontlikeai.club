import org.apache.pdfbox.pdmodel.PDDocument;
import org.apache.pdfbox.pdmodel.PDPage;
import org.apache.pdfbox.pdmodel.PDPageContentStream;
import org.apache.pdfbox.pdmodel.font.PDType0Font;
import java.io.FileInputStream;
import java.io.IOException;

public class CreateDoc {
    // private fields hold filePath text for use through class
    private String filePath;
    private String secured;

    // one-arg constructor to construct object and set filePath name
    public CreateDoc(String filePath, String secured){
        this.filePath = filePath;
        this.secured = secured;
    }

    public void create() throws IOException{
        PDDocument document = new PDDocument();
        createPage(document);
        document.save(this.filePath);
        document.close();
    }

    //create a document with the number of pages as the imported doc
    public void createPage(PDDocument document) throws IOException{
        PDPage page = new PDPage();
        document.addPage(page);
        writeToFile(document, page);

    }

    // write to document
    public void writeToFile(PDDocument document, PDPage page) throws IOException {
        PDPageContentStream stream = new PDPageContentStream(document, page);
        stream.beginText();
        PDType0Font font = PDType0Font.load(document, new FileInputStream("C:/Windows/Fonts/arial.ttf"));
        stream.setFont(font, 12);
        stream.newLineAtOffset(50, 700);
        System.out.println(this.secured);
        stream.showText(this.secured);
        stream.endText();
        stream.close();
    }
}
