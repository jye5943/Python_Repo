
public class total_0322 {
	public static void main(String[] args) {
 
 
// 방법1. 총합 - 짝수 = 홀수 합
 

int total = 0;
int evenTotal = 0;
int oddTotal = 0;

for (int i = 0; i < 100; i++) {
	int number = i + 1;
	total = total + number ;
	
	
	int evenNumber = 0;
	int oddNumber = number;
	

	if ( number %2 == 0) {
		evenNumber = number;
		oddNumber = 0;
	}
		
		evenTotal = evenTotal + evenNumber;
		oddTotal =oddTotal + oddNumber; 
} 
	oddTotal = total - evenTotal;
	  System.out.println("총합은 " + total);
	  System.out.println("홀수 총합은 " + evenTotal);
	  System.out.println("짝수 총합은 " + oddTotal);
}}