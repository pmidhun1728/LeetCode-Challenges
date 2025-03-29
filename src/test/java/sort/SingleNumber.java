package sort;
import java.util.HashSet;
import java.util.Set;

public class SingleNumber{

    public static void main(String args[]) {

        int[] nums = {1, 2, 2, 4, 5, 5, 6};
        Set<Integer> result = findDuplicates(nums);
        System.out.println("Number of distinct duplicates: " + result);

        // Print the duplicate elements
        System.out.println("Distinct duplicates: " + findDuplicates(nums));
        }

public static Set<Integer> findDuplicates(int[] nums) {
        Set<Integer> uniqueNumbers = new HashSet<>();
        Set<Integer> duplicates = new HashSet<>();

        for (int num: nums) {
        if (!uniqueNumbers.add(num)) {
        duplicates.add(num);
        }
        }
        return duplicates;
        }
}