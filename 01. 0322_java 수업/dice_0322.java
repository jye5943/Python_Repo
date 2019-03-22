import java.util.Random;
import java.util.Scanner;


//방법 1) 
//멀쩡하게 동작을 하는지 테스트를 해본 수에 반복되는 걸 for문으로 만듦 -> for문에서 빠져나갈 때 break 를 만듦 ->중요한 포인드
public class dice_0322 {
	public static void main(String[] args) {
			int comDice = 0 ;
			int userDice = 0;
			
		Random rand = new Random();
		Scanner scan = new Scanner(System.in);
//			
//	
//	     for (int i =0; i < 100000; i++) {
//	     System.out.println("컴퓨터의 주사위를 굴릴까요? (종료하실려면 q을 입력하세요)"};
//			String inputString = scan.nextLine();
//			//문자랑 문자랑 비교해야하기 때문에 ignorance가 들어간거임
//	
//					
//			int inputNumber = scan.nextInt();
//			if(inputNumber == 1) []
//					 System.out.println("게임이 종료되었습니다.");

		//아래만 반복을 시켜주면 되니까 for문 생성 (for문은 위에 주석처리 했는데 오류남- > 교수님 답안 보기)	
				
			System.out.println("컴퓨터의 주사위를 굴릴까요?");
			scan.nextLine();
			
		//컴퓨터	
			comDice = rand.nextInt(6) + 1;
			
			System.out.println("컴퓨터의 주사위는" + comDice + "입니다.");
			
		//사용자 
			System.out.println("사용자의 주사위를 굴릴까요?");
			scan.nextLine();
			
			
			comDice = rand.nextInt(6) + 1;
			
			System.out.println("사용자의 주사위는" + userDice + "입니다.");
			
			if (comDice == userDice) {
				System.out.println("비겼습니다");
			}
			
			else if(comDice > userDice) {
				System.out.println("컴퓨터가 이겼습니다");
			} 
			
	    else if(comDice < userDice) {
		System.out.println("사용자가 이겼습니다");
	}
			
	}
}
