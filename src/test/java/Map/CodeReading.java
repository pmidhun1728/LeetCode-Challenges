package Map;

import java.util.HashSet;
import java.util.Set;

class Pair {
    int x;
    int y;

    Pair(int x, int y) {
        this.x = x;
        this.y = y;
    }
}

public class CodeReading {
    public static void findPairs(Pair[] pairs) {
        Set<String> set = new HashSet<>();

        for (Pair curr_pair : pairs) {
            String pairStr = curr_pair.x + "," + curr_pair.y;
            String revPairStr = curr_pair.y + "," + curr_pair.x;

            if (set.contains(revPairStr))
                System.out.println(pairStr + " " + revPairStr);

            set.add(pairStr);
        }
    }

    public static void main(String[] args) {
        Pair[] pairs = new Pair[] {
                new Pair(3, 4),
                new Pair(1, 2),
                new Pair(5, 2),
                new Pair(4, 3),
                new Pair(2, 5),
                new Pair(2, 7)
        };
        findPairs(pairs);
    }
}

