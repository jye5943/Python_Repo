import java.util.Arrays;

public class class_0322 {
public static void main(String[] args) {

	//length는 배열의 길이
	int[] arr = {1,2,3,4,5};
	for (int i = 0; i < arr.length; i++) {
		System.out.println(arr[i]);
}

	 
		int[] arr2 = arr; 
		int[] arr3 = arr2;
		arr3[0]= 10;
		System.out.println(Arrays.toString(arr));

			
		
   for( int i =0; i < arr.length; i++) {
	System.out.print(arr[1]);
	System.out.print(" ");
}

   
}
}