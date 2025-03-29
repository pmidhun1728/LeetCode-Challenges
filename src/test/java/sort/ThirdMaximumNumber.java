package sort;
import java.util.Arrays;
import java.util.List;
import java.util.stream.Collectors;

public class ThirdMaximumNumber {
    public static Integer thirdMax(int[] nums) {
        List<Integer> distinctValues = Arrays.stream(nums)
                .distinct()
                .boxed()
                .sorted((a, b) -> b - a) // Sort in descending order
                .collect(Collectors.toList());

        return distinctValues.size() >= 3 ? distinctValues.get(2) : distinctValues.get(0);
    }

    public static void main(String[] args) {
        int[] num = {3, 2, 1};
        System.out.println("Output for " + Arrays.toString(num) + " is: " + thirdMax(num));
    }
}
