import java.io.File;
import java.io.IOException;

import org.apache.pdfbox.cos.COSDocument;
import org.apache.pdfbox.pdmodel.PDDocument;
import org.apache.pdfbox.pdmodel.PDPage;
import org.apache.pdfbox.pdmodel.PDPageContentStream;
import org.apache.pdfbox.pdmodel.font.PDFont;
import org.apache.pdfbox.pdmodel.font.PDSimpleFont;
import org.apache.pdfbox.pdmodel.font.PDType1Font;
import org.apache.pdfbox.pdmodel.font.Standard14Fonts;
import org.apache.pdfbox.Loader;
import org.apache.pdfbox.text.PDFTextStripper;

import static org.apache.pdfbox.pdmodel.font.PDType1Font.*;
import static org.apache.pdfbox.pdmodel.font.Standard14Fonts.FontName.TIMES_ROMAN;

public class CreateDoc {
    private String filePath;

    public CreateDoc(String filePath){
        this.filePath = filePath;
    }

    public void create() throws IOException{
        PDDocument document = new PDDocument();
        createPage(document);
        document.save(this.filePath);
        document.close();
    }

    public void createPage(PDDocument document) throws IOException{
        PDPage page = new PDPage();
        document.addPage(page);
        writeToFile(document, page);
    }

    public void writeToFile(PDDocument document, PDPage page) throws IOException{
        PDPageContentStream stream = new PDPageContentStream(document, page);
        stream.beginText();
        PDType1Font font = new PDType1Font(TIMES_ROMAN);
        stream.setFont(font, 12);
        stream.newLineAtOffset(50, 700);
        stream.showText("Hello! This is a document I created with Java");
        stream.newLineAtOffset(0, -15);
        stream.showText("I am very excited because this is the first time I have tried this!");
        stream.newLineAtOffset(0, -15);
        stream.showText("How are you?");
        stream.newLineAtOffset(0, -15);
        stream.showText("I'm doing great");
        stream.endText();
        stream.close();
    }
}
