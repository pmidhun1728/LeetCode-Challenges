package Map;

import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Scanner;

public class MaxRepeatCount {

    public static void main(String[] args) {
        Scanner scanner = new Scanner(System.in);
        System.out.print("Enter the String Value: ");
        String sc = scanner.nextLine();


        Map<Character, Integer> map = new LinkedHashMap<>();
       for(char c: sc.toCharArray()) {
           map.put(c, map.getOrDefault(c, 0) + 1);
       }
        char maxChar = ' ';
        int maxCount = 0;

        for(Map.Entry<Character, Integer> entry: map.entrySet()){
            if(entry.getValue()>maxCount){
                maxCount =entry.getValue();
                maxChar = entry.getKey();
            }
        }
        System.out.println("Character-"+maxChar + " Count is : "+maxCount);
    }
}
