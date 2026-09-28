console.log("LOGIN JS LOADED");
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
            headers: {
                "Content-Type": "application/x-www-form-urlencoded"
            },
            body: formData
        });

        const data = await response.json();
        console.log("LOGIN STATUS:", response.status);
        console.log("LOGIN RESPONSE:", data);

        if (!response.ok) {
            errorMessage.textContent = data.detail || "Login failed";
            return;
        }

        // Save JWT
        localStorage.setItem("access_token", data.access_token);

        console.log("Login successful");

        const token = localStorage.getItem("access_token");

        const profileResponse = await fetch("/profile", {
    headers: {
        "Authorization": `Bearer ${token}`
    }
});

const profile = await profileResponse.json();

console.log("PROFILE:", profile);

        // We'll decide the final destination later
        window.location.href = "/";

    } catch (error) {
        console.error("Login error:", error);
        errorMessage.textContent = "Something went wrong";
    }
});