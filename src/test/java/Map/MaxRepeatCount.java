package Map;

import javax.sound.sampled.Line;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Scanner;

public class MaxRepeatCount {

    public static void main(String[] args) {
        Scanner scanner = new Scanner(System.in);
       String sc = scanner.nextLine();

       char maxChar = ' ';
       int maxCount = 0;

        Map<Character, Integer> map = new LinkedHashMap<>();

       for(char c: sc.toCharArray()){

         map.put(c, map.getOrDefault(c, 0)+1);

         if(map.get(c)> maxCount){

             maxCount= map.get(c);
             maxChar =c;
         }

       }
        System.out.println(maxChar +" : "+ maxCount);

    }
}
