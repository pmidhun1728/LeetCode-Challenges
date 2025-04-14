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

        
    }
}