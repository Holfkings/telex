// @ts-nocheck
import axios from "axios";

export function configureClient() {
  axios.defaults.baseURL = "https://api.example.com";
  axios.defaults.headers.common = { Authorization: "Bearer token123" };
}
