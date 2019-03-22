import java.util.Scanner;

public class string_0322 {
public static void main(String[] args) {
	String a ="hello";
    String b ="hello";
    Scanner scan = new Scanner(System.in);
    String c = scan.nextLine();
    
    
    System.out.println(a == b); 
    System.out.println(a.equals(c));
  
    //equals는 무조건 문자열이 같은지만 비교해주는거임
    
    System.out.println(a.hashCode());
    System.out.println(a.hashCode());
}
}
