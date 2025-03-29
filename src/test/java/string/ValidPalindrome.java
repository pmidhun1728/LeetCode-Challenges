package string;
public class ValidPalindrome {

    public static void main(String args[]) {

        if (isPalindrome("race a car")) {
            System.out.print("Is Not Valid");
        } else {
            System.out.print("Is Valid");
        }
    }

    public static Boolean isPalindrome(String s) {

        if (s == null || s.isBlank()) {
            return true;
        }

        s = s.replaceAll("[^A-Za-z0-9]", "").toLowerCase();
        int strLength = s.length();
        for (int i = 0; i < strLength / 2; i++) {
            if (s.charAt(i) != s.charAt(strLength - i - 1)) {
                return false;
            }
        }
        return true;
    }
}
