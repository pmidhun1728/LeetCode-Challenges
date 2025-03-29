package Map;

import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Random;
import java.util.Scanner;

public class CharacterCount {

    public static void main(String[] args) {
        
        Scanner scanner = new Scanner(System.in);
        String sc = scanner.nextLine();

        Map<Character, Integer> map  = new LinkedHashMap<>();

        for(char c: sc.toCharArray()){
            map.put(c, map.getOrDefault(c, 0)+1);
        }
        for(Map.Entry<Character, Integer> entry : map.entrySet()){
            System.out.println(entry.getKey() + " : "  + entry.getValue());
        }
    }
}
