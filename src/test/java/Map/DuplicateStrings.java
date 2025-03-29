package Map;

import java.util.LinkedHashMap;
import java.util.Map;

public class DuplicateStrings {
    public static void main(String[] args) {
        String[] str = {"Jack", "Jack", "Will", "smith",};
        Map<String, Integer> map = new LinkedHashMap<>();

        for(String ch: str){
            map.put(ch, map.getOrDefault(ch, 0)+1);
        }
        for(Map.Entry<String,Integer> entry: map.entrySet()){
            if(entry.getValue()>1){
                System.out.println(entry.getKey()+ " : "+ entry.getValue());
            }
        }
    }
}
