package Map;

import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Scanner;

public class FirstNonRepeatCharacter {

    public static void main(String[] args) {

        Scanner scanner = new Scanner(System.in);
        String sc = scanner.nextLine();

        Map<Character, Integer> map = new LinkedHashMap<>();
        for(char c: sc.toCharArray()){
            map.put(c, map.getOrDefault(c, 0)+1);
        }

        for(Map.Entry<Character, Integer> entry : map.entrySet()){
            if(entry.getValue()==1){
                System.out.println(entry.getKey()+" : "+entry.getValue());
                break;
            }
        }
    }
}
