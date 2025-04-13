package Streams;

import java.util.Arrays;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

class Employee {
    String name;
    String department;

    Employee(String name, String department) {
        this.name = name;
        this.department = department;
    }
}
public class GroupByDepartment {
    public static void main(String[] args) {
        List<Employee> employees = Arrays.asList(
                new Employee("Alice", "HR"),
                new Employee("Bob", "Engineering"),
                new Employee("Charlie", "HR"),
                new Employee("David", "Engineering"),
                new Employee("Eve", "Sales")
        );

        Map<String, List<Employee>> grouped = employees.stream()
                .collect(Collectors.groupingBy(emp -> emp.department));

        grouped.forEach((dept, empList) -> {
            System.out.println(dept + ": " + empList.stream().map(emp -> emp.name).collect(Collectors.toList()));
        });
    }
}
