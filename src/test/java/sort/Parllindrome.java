package sort;
public class Parllindrome {

    public static boolean isPalindrome(String str) {
        String cleanedStr = str.replaceAll("[^a-zA-Z0-9]", "").toLowerCase();
        String reversedStr = new StringBuilder(cleanedStr).reverse().toString();
        return cleanedStr.equals(reversedStr);
    }

    public static void main(String[] args) {
        String test1 = "AAA";
        String test2 = "AB";

        System.out.println(test1 + " is a palindrome? " + isPalindrome(test1)); // true
        System.out.println(test2 + " is a palindrome? " + isPalindrome(test2)); // false
    }
}
