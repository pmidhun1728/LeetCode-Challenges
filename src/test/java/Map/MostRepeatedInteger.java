package Map;

import java.util.*;

public class MostRepeatedInteger {

    public static void main(String[] args) {

        List<Integer> list = Arrays.asList(1, 1, 2, 2, 2, 3);

        Map<Integer, Integer> map = new HashMap<>();
        int maxCount = 0;
        int mostRepeated = list.get(0);

        for (int num : list) {
            int count = map.getOrDefault(num, 0) + 1;
            map.put(num, count);

            if (count > maxCount) {
                maxCount = count;
                mostRepeated = num;
            }
        }

        System.out.println("Most repeated integer: " + mostRepeated + " (repeated " + maxCount + " times)");
    }
}
