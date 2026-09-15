// @ts-nocheck
import jwt from "jsonwebtoken";

export function authenticate(token: string, secret: string) {
  return jwt.verify(token, secret);
}
