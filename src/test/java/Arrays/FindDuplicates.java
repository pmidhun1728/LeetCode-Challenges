package Arrays;

import java.util.HashSet;
import java.util.Set;

public class FindDuplicates {
    public static void main(String[] args) {
        int[] nums = {1, 2, 3, 2, 4, 5, 1};
        Set<Integer> set = new HashSet<>();
        for (int num : nums) {
            if (!set.add(num)) {
                System.out.println("Duplicate: " + num);
            }
        }
    }
}
