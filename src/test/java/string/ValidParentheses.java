package string;
import java.util.Scanner;

public class ValidParentheses {

    public static void main(String[] args){

        Scanner scanner = new Scanner(System.in);
        String sc = scanner.next();

        if(isValid(sc)){
            System.out.println("Valid");
        }else{
            System.out.println("Not Valid");
        }

    }
    public static boolean isValid(String S) {

        String s= "()[]{}";
        if(s.contains("()")){


        }else{
            System.out.println("Not Valid");
        }
        return false;
    }
}