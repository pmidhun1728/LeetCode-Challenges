package Streams;

import java.util.*;
import java.util.stream.*;

public class StreamPractice {

    public static void main(String[] args) {

        List<String> names = Arrays.asList("John", "Alice", "Bob", "Michael", "Sarah", "David", "Sophia");

        // 1. Filter names that start with "S"
        List<String> namesStartingWithS = names.stream()
                .filter(name -> name.startsWith("S"))
                .collect(Collectors.toList());
        System.out.println("Names starting with S: " + namesStartingWithS);

        // 2. Map names to uppercase
        List<String> upperCaseNames = names.stream()
                .map(String::toUpperCase)
                .collect(Collectors.toList());
        System.out.println("Uppercase Names: " + upperCaseNames);

        // 3. Sort names alphabetically
        List<String> sortedNames = names.stream()
                .sorted()
                .collect(Collectors.toList());
        System.out.println("Sorted Names: " + sortedNames);

        // 4. Reduce - concatenate all names
        String concatenatedNames = names.stream()
                .reduce("", (a, b) -> a + " " + b);
        System.out.println("Concatenated Names: " + concatenatedNames.trim());

        // 5. Count names longer than 4 characters
        long count = names.stream()
                .filter(name -> name.length() > 4)
                .count();
        System.out.println("Count of names longer than 4 characters: " + count);

        // 6. Create a list of numbers
        List<Integer> numbers = Arrays.asList(3, 7, 2, 9, 4, 7, 10, 2);

        // 7. Find unique even numbers and sort
        List<Integer> uniqueEvenNumbers = numbers.stream()
                .filter(num -> num % 2 == 0)
                .distinct()
                .sorted()
                .collect(Collectors.toList());
        System.out.println("Unique Even Numbers: " + uniqueEvenNumbers);

        // 8. Group numbers by even and odd
        Map<String, List<Integer>> evenOddMap = numbers.stream()
                .collect(Collectors.groupingBy(num -> num % 2 == 0 ? "Even" : "Odd"));
        System.out.println("Grouped by Even and Odd: " + evenOddMap);

        // 9. Find max number
        numbers.stream()
                .max(Integer::compareTo)
                .ifPresent(max -> System.out.println("Max Number: " + max));

        // 10. Sum of all numbers
        int sum = numbers.stream()
                .mapToInt(Integer::intValue)
                .sum();
        System.out.println("Sum of Numbers: " + sum);
    }
}
