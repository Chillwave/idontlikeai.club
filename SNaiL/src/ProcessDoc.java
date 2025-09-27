import java.util.List;
import java.util.Random;

public class ProcessDoc {
    private String text;

    public ProcessDoc(String text){
        this.text = text;
    }

    public String process(){
        String result = "";
        DocHash hash = new DocHash();
        for(int i = 0; i < this.text.length(); i++){
            if(Character.isLetter(this.text.charAt(i)) && (this.text.toUpperCase().charAt(i)) != (this.text.charAt(i))){
                Random rand = new Random();

                List<Character> temp = hash.getChars(this.text.charAt(i));
                result += temp.get(rand.nextInt(temp.size()));
            }
            else{
                result += this.text.charAt(i);
            }
        }

        return result;
    }
}
