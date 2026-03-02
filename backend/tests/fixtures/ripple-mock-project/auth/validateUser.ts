import { User } from "../shared/types";

export function validateUser(user: User): boolean {
    return user.id !== null;
}
