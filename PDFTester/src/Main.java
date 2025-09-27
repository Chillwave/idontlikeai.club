import java.io.IOException;

public class Main {
    public static void main(String[] args) {
        String filePath = "C:/Users/School/Documents/ShellHacks2025/my_doc.pdf";
        CreateDoc created = new CreateDoc(filePath);

        try{
            created.create();
        }
        catch(IOException e){
            System.out.println(e.getMessage());
        }

        ImportDoc imported = new ImportDoc(filePath);

        try{
            imported.printEncoded(imported.getContents());
        }
        catch(IOException e){
            System.out.println(e.getMessage());
        }

    }
}
