import org.springframework.web.bind.annotation.RestController;
import java.util.List;
public class ServiceController 
{
    public void hello() 
    {
        helper();
    }
    private void helper() 
    {}
    private int add(int a, int b) 
    {
        return a + b;
    }
}

