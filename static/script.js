import { setAccessToken } from "./api.js";

const loginForm = document.querySelector("#loginForm");
const errorMessage = document.querySelector("#errorMessage");

loginForm.addEventListener("submit", async function (event) {
    event.preventDefault();

    const username = document.querySelector("#username").value;
    const password = document.querySelector("#password").value;

    const formData = new URLSearchParams();
    formData.append("username", username);
    formData.append("password", password);

    try {
        const response = await fetch("/login", {
            method: "POST",
            credentials: "include", // lets the browser save the refresh cookie
            body: formData,
        });

        const data = await response.json();

        if (!response.ok) {
            errorMessage.textContent = data.detail || "Login failed";
            return;
        }

        setAccessToken(data.access_token);
        window.location.href = "/";
    } catch (error) {
        console.error("Login error:", error);
        errorMessage.textContent = "Something went wrong";
    }
});