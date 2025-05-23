package sort;

import java.util.Scanner;

public class PrimeChecker {

    public static boolean isPrime(int number) {
        if (number <= 1) {
            return false;
        }

        for (int i = 2; i <= Math.sqrt(number); i++) {
            if (number % i == 0) {
                return false;
            }
        }
        return true;
    }

    public static void main(String[] args) {
        Scanner scanner = new Scanner(System.in);
        System.out.print("Enter the Scanner Number: ");
        int scannerInt = scanner.nextInt();

        if (isPrime(scannerInt)) {
            System.out.println(scannerInt + " is a prime number.");
        } else {
            System.out.println(scannerInt + " is not a prime number.");
        }
    }
}

