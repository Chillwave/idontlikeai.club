import java.util.Map;
import java.util.HashMap;
import java.util.List;
import java.util.ArrayList;
import java.util.Arrays;

public class DocHash {
    private Map<Character, List<Character>> charHash;

    public DocHash(){
        // initialize character hash
        charHash = new HashMap<>();

        // set up characters hash for use
        charHash.put('a', new ArrayList<>(Arrays.asList('а', 'ạ', 'ą', 'ä', 'à', 'á', 'ą')));
        charHash.put('b', new ArrayList<>(Arrays.asList('b')));
        charHash.put('c', new ArrayList<>(Arrays.asList('с', 'ƈ', 'ċ')));
        charHash.put('d', new ArrayList<>(Arrays.asList('ԁ', 'ɗ')));
        charHash.put('e', new ArrayList<>(Arrays.asList('е', 'ẹ', 'ė', 'é', 'è')));
        charHash.put('f', new ArrayList<>(Arrays.asList('f')));
        charHash.put('g', new ArrayList<>(Arrays.asList('ġ')));
        charHash.put('h', new ArrayList<>(Arrays.asList('һ')));
        charHash.put('i', new ArrayList<>(Arrays.asList('і', 'í', 'ï')));
        charHash.put('j', new ArrayList<>(Arrays.asList('ј', 'ʝ')));
        charHash.put('k', new ArrayList<>(Arrays.asList('κ')));
        charHash.put('l', new ArrayList<>(Arrays.asList('ӏ', 'ḷ')));
        charHash.put('m', new ArrayList<>(Arrays.asList('m')));
        charHash.put('n', new ArrayList<>(Arrays.asList('ո')));
        charHash.put('o', new ArrayList<>(Arrays.asList('о', 'ο', 'օ', 'ȯ', 'ọ', 'ỏ', 'ơ', 'ó', 'ò', 'ö')));
        charHash.put('p', new ArrayList<>(Arrays.asList('p')));
        charHash.put('q', new ArrayList<>(Arrays.asList('զ')));
        charHash.put('r', new ArrayList<>(Arrays.asList('r')));
        charHash.put('s', new ArrayList<>(Arrays.asList('ʂ')));
        charHash.put('t', new ArrayList<>(Arrays.asList('t')));
        charHash.put('u', new ArrayList<>(Arrays.asList('υ', 'ս', 'ü', 'ú', 'ù')));
        charHash.put('v', new ArrayList<>(Arrays.asList('ν', 'ѵ')));
        charHash.put('w', new ArrayList<>(Arrays.asList('w')));
        charHash.put('x', new ArrayList<>(Arrays.asList('х', 'ҳ')));
        charHash.put('y', new ArrayList<>(Arrays.asList('у', 'ý')));
        charHash.put('z', new ArrayList<>(Arrays.asList('ʐ', 'ż')));

    }

    // getter to call hash externally
    public List getChars(Character c){
        return charHash.get(c);
    }
}
