package sort;
import java.util.HashMap;
import java.util.Map;

public class SingleNumberII {
    public static int singleNumber(int[] nums) {
        Map<Integer, Integer> map = new HashMap<>();

        for (int num : nums) {
            map.put(num, map.getOrDefault(num, 0) + 1);
        }

        for (Map.Entry<Integer, Integer> entry : map.entrySet()) {
            if (entry.getValue() == 1) {
                return entry.getKey();
            }
        }
        throw new IllegalArgumentException("No single number found");
    }

    public static void main(String[] args) {
        int[] nums1 = {2, 2, 3, 2};
        int[] nums2 = {0, 1, 0, 1, 0, 1, 99};

        System.out.println("Single number in nums1: " + singleNumber(nums1));
        System.out.println("Single number in nums2: " + singleNumber(nums2));
    }
}
