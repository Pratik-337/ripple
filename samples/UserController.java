public class UserController {
   
        // This is the field declaration we want our parser to find.
        private UserService myUserService;
   
        public void handleUserRequest() {
            // This is the cross-file method call we want to resolve.
            myUserService.getUsers();
        }
   
        // NEW METHOD: To test local variable resolution
        public void handleLocalService() {
            UserService localService = new UserService(); // This is a local variable
            localService.getUsers(); // We want to resolve this call
        }
   }