package Map;

import java.util.HashMap;
import java.util.Map;

public class PairSumCounter {

    public static int countPairsWithSum(int[] nums, int target) {
        Map<Integer, Integer> map = new HashMap<>();
        int count = 0;

        for (int num : nums) {
            int complement = target - num;
            if (map.containsKey(complement)) {
                count += map.get(complement);
            }

            map.put(num, map.getOrDefault(num, 0) + 1);
        }

        return count;
    }

   
}
