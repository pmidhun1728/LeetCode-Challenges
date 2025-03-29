package sort;
public class StackPrefix {
    public static String reversePrefix(String word, char ch) {
        int index = word.indexOf(ch);

        if (index == -1) {
            return word;
        }
        String reversedPrefix = "";
        for (int i = index; i >= 0; i--) {
            reversedPrefix += word.charAt(i);
        }

        String result = reversedPrefix + word.substring(index + 1);

        return result;
    }

    public static void main(String[] args) {
        String word = "abcdef";
        char ch = 'd';
        System.out.println(reversePrefix(word, ch));
    }
}
