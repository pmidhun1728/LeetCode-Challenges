package string;
import java.util.Scanner;

public class StringCheck {

    public static void main(String args[]){

        Scanner scanner = new Scanner(System.in);
        String sc = scanner.next();

        if(isPalindrome(sc)){
            System.out.println("Is not Palindrome");
        }
        else{
            System.out.println("is a Palindrome");
        }

    }

    public static Boolean isPalindrome(String str){

        int s = str.length();
        for(int i=0; i<s; i++){
            if(str.charAt(i)==str.charAt(s-i-1)){
                return false;
            }

        }

        return true;
    }
}
