public class Main {
    public static void main(String[] args) {
        String filePath = "C:/Users/School/Documents/ShellHacks2025/my_doc";
        ImportDoc imported = new ImportDoc(filePath + ".pdf");

        try{
            ProcessDoc processed = new ProcessDoc(imported.getContents());
            CreateDoc created = new CreateDoc(filePath + "_secured.txt", processed.process());
            created.create();
        }
        catch(Exception e){
            System.out.println("Error: " + e.getMessage());
        }
    }
}
