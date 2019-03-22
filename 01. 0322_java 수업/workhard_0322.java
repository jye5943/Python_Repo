import java.util.Arrays;
import java.util.Scanner;

//10명의 국어점수 입력받아서 입력된 값 출력 및 총점, 평균
public class workhard_0322 {

	public static void main(String[] args) {
		
//		System.out.println("10명의 국어 점수를 입력하세요.");
//	    Scanner scan = new Scanner();
//	    for (i=0; i<9; i++ ); {
//	    	
//	    
//	    Random r = new Random();
//	    int randomValue = r. nextInt(100);
//	    System.out.println(randomValue);
//	    }
		Scanner scan = new Scanner(System.in);
//새로생성할때는 new라고 입력하고, int[] 안에 grades라는 변수를 넣어준다
		int [] grades = new int[10]; //10개의 int를 만든다 
		for(int i =0; i < grades.length; i++) {
			System.out.println(i + "성적 점수를 넣어주세요.");
			int userInput = scan.nextInt();
			grades[i] = userInput;
		}
	
//교수님 답안
//		int [] score = new int [10];
//		
//		Scanner scan1 = new Scanner(System.in);
//		
//		for (int i = 0; i< grades.length; i++) {
//			System.out.print("국어점수: ");
//			score[i] = scan1.nextInt();
//		}
//		System.out.println(Arrays.toString(score));
//		
//		int total = 0;
//		double avr = 0;
//		
//		입력받는 부분과 수정하는 부분, 출력하는 부분을 각각 만드는게 좋음
//		for (int i =0; i < score.length; i++) {
//			total = total + score[i];
//		}
//	//double로 캐스팅을 꼭 시켜주기!
//		avr = (double)total / score.length;
//		
//	System.out.println("총점은 : "+total);
//	System.out.println("평균은 : "+avr);



		
		
//추가 미션 : 이름, 국어점수, 수학점수, 영어점수를 입력 받아서 각각의 점수출격 각각의 총점/ 평균 출력 해보시오.

	}
}
