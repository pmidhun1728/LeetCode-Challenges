package Streams;

import java.util.*;

public class SecondHighestSalary {
    public static void main(String[] args) {
        List<Integer> salaries = Arrays.asList(5000, 7000, 12000, 7000, 10000, 12000, 9000);

        Optional<Integer> secondHighest = salaries.stream()
                .distinct()
                .sorted(Comparator.reverseOrder())
                .skip(1)
                .findFirst();

        secondHighest.ifPresent(salary -> System.out.println("Second Highest Salary: " + salary));
    }
}
