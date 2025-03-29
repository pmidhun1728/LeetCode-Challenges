package sort;
public class SubStrings {
    public static int numOfStrings(String[] patterns, String word) {

        word ="abc";
        patterns = new String[]{"a","abc","bc","d"};
        for(String pattern: patterns){
            if(word.contains(pattern)){
              String result= String.valueOf(patterns);
                System.out.println(pattern + ": appears as a substring in:"+ word);
            } else{
                System.out.println(pattern + ": does not appear as a substring in"+ word);
            }
        }
        return 0;
    }

   public static  void main(String args[]){

       String[] pattens = {""};
       String word ="";
       int s = numOfStrings(pattens, word);
       System.out.println("Total patterns that appear as substrings: " + s);

   }
}
