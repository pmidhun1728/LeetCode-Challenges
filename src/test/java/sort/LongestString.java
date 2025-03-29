package sort;

import java.util.HashMap;

public class LongestString {
    public static int lengthOfLongestSubstring(String s) {
        if (s == null || s.length() == 0) {
            return 0;
        }

        HashMap<Character, Integer> map = new HashMap<>();
        int maxLength = 0;
        int start = 0;

        for (int end = 0; end < s.length(); end++) {
            char currentChar = s.charAt(end);

            if (map.containsKey(currentChar)) {
                start = Math.max(start, map.get(currentChar) + 1);
            }

            map.put(currentChar, end);
            maxLength = Math.max(maxLength, end + 1 - start);
        }

        return maxLength;
    }

    public static void main(String[] args) {
        String s = "abcabcbb";
        System.out.println("Length of longest substring without repeating characters: " + lengthOfLongestSubstring(s));  // Output: 3 ("abc")

        s = "bbbbb";
        System.out.println("Length of longest substring without repeating characters: " + lengthOfLongestSubstring(s));  // Output: 1 ("b")

        s = "pwwkew";
        System.out.println("Length of longest substring without repeating characters: " + lengthOfLongestSubstring(s));  // Output: 3 ("wke")
    }
}

