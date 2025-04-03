package Map;
import java.util.Arrays;

public class Anagram {
    public static void main(String[] args) {

        String s1 = "listen";
        String s2 = "silent";

        char[] str1 = s1.toLowerCase().toCharArray();
        char[] str2 = s2.toLowerCase().toCharArray();

        Arrays.sort(str1);
        Arrays.sort(str2);

        if(Arrays.equals(str1, str2)){
            System.out.println(s1 + " and " + s2 + " are anagrams.");
        }else{
            System.out.println(s1 + " and " + s2 + " are not anagrams.");
        }
    }
}
