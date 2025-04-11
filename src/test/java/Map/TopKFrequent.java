package Map;

import java.util.*;

public class TopKFrequent {
    public static void main(String[] args) {
        int[] nums = {1,1,1,2,2,3};
        int k = 2;

        Map<Integer, Integer> freqMap = new HashMap<>();
        for (int num : nums) {
            freqMap.put(num, freqMap.getOrDefault(num, 0) + 1);
        }

        PriorityQueue<Map.Entry<Integer, Integer>> heap = new PriorityQueue<>(
                (a, b) -> b.getValue() - a.getValue()
        );

        heap.addAll(freqMap.entrySet());

        for (int i = 0; i < k; i++) {
            System.out.println(heap.poll().getKey());
        }
    }
}
