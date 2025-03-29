package string;
import java.util.Arrays;
import java.util.List;
import java.util.Scanner;
import java.util.stream.Collectors;

public class LongestCommonPrefix {
    public static void main(String[] args) {

        Scanner scanner = new Scanner(System.in);
        String sc =scanner.next();
        String sc1 =scanner.next();
        String sc2 = scanner.next();

        List<String> s = Arrays.asList(sc,sc1,sc2);

        List<String> l = s.stream()
                        .map(x->x.length()>2 ? x.substring(0,2): x)
                        .collect(Collectors.toList());


        boolean matching = l.stream().distinct().count()==1;

           if(matching){
               System.out.println(l+ ":All the content is matching");
           }else{
               System.out.println(l+ ":No prefix is matching");

       }
    }
}


