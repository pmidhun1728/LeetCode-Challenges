package sort;

class BubbleSort {
    public static void main(String[] args) {

        int temp =0;
        int[] input = {4,5,2,10,6,5};
        int size = input.length;

        for(int i=0; i<size; i++){
            for(int j=0; j< size-i-1; j++){
                if(input[j]> input[j+1]){
                    temp = input[j];
                    input[j]= input[j+1];
                    input[j+1]= temp;
                }
            }
        }
        System.out.println("After Sorting: ");

        for(int num: input){
            System.out.print(num + " ");

        }    }
}
