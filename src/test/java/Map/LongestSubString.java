package Map;

import java.util.LinkedHashMap;
import java.util.Map;

public class LongestSubString {

    public static void main(String[] args) {
        String str= "abcabbc";
        String longest = "";

        Map<Character, Integer> map = new LinkedHashMap<>();

        for(int i=0; i<str.length(); i++){
           char ch = str.charAt(i);

           if(map.containsKey(ch)){
              i = map.get(ch);
              map.clear();
           }else{
               map.put(ch, i);
               if(map.size() > longest.length()){
                    longest ="";

                    for(char c: map.keySet()){
                        longest +=c;
                    }
               }
           }
        }
        System.out.println(longest);
    }

}