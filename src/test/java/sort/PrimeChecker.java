package sort;

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
        int input = 29;

        if (isPrime(input)) {
            System.out.println(input + " is a prime number.");
        } else {
            System.out.println(input + " is not a prime number.");
        }
    }
}

