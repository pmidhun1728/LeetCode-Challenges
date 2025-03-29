package sort;
import java.util.Arrays;
import java.util.List;
import java.util.stream.Collectors;

public class Streams {

    public static void main(String args[]){

        List<Integer> list = Arrays.asList(1,2, 2, 3,4,5,6,7,8,9,10);

       List<String> listString = list.stream().map(x-> x%2==0 ? x+ " : is even": "odd: "+ x)
                .collect(Collectors.toList());

        System.out.println(listString);

    }
}
