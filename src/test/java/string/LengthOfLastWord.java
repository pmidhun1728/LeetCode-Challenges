package string;

public class LengthOfLastWord {
    public static int lengthOfLastWord(String s) {

        String[] sc = s.trim().split(" ");
        String lastWord = sc[sc.length-1];
        int length = lastWord.length();
        System.out.println(length);

        return length;
    }

    public static void main(String[] args){
        lengthOfLastWord("");
    }
}