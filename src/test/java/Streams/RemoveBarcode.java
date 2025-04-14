package Streams;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

public class RemoveBarcode {
    public static class Sample {
        private final String barcode;
        private final int id;

        public Sample(String barcode, int id) {
            this.barcode = barcode;
            this.id = id;
        }

        public String getBarcode() {
            return barcode;
        }

        public int getId() {
            return id;
        }
    }

    public static void main(String[] args) {
        // Step 1: Create list and add samples
        List<Sample> sampleList = new ArrayList<>();
        sampleList.add(new Sample("ABC", 1));
        sampleList.add(new Sample("DEF", 2));
        sampleList.add(new Sample("ABC", 3));
        sampleList.add(new Sample("XYZ", 4));

        // Step 2: Remove samples where barcode is not "ABC"
        sampleList.removeIf(sample -> !sample.getBarcode().equals("ABC"));

        // Step 3: Add one more sample with barcode "ABC" and id = maxId + 1
        int maxId = sampleList.stream()
                .mapToInt(Sample::getId)
                .max()
                .orElse(0); // fallback to 0 if list is empty
        sampleList.add(new Sample("ABC", maxId + 1));

        // Step 4: Convert to Map<barcode, id>
        Map<String, Integer> sampleMap = new HashMap<>();
        for (Sample sample : sampleList) {
            sampleMap.put(sample.getBarcode(), sample.getId());
        }

        // Step 5: Print map values
        for (Map.Entry<String, Integer> entry : sampleMap.entrySet()) {
            System.out.println("Barcode: " + entry.getKey() + ", ID: " + entry.getValue());
        }
    }
}