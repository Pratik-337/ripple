import React from "react";
import { validateUser } from "../auth/validateUser";

export const UserPanel = ({ user }) => {
    const isValid = validateUser(user);
    return <div>User is {isValid ? "Valid" : "Invalid"}</div>;
};
