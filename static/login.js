const loginForm = document.querySelector("#loginForm");
const errorMessage = document.querySelector("#errorMessage");

loginForm.addEventListener("submit", async function (event) {
    event.preventDefault();

    const formData = new URLSearchParams();
    formData.append("username", document.querySelector("#username").value);
    formData.append("password", document.querySelector("#password").value);

    try {
        const response = await fetch("/login", {
            method: "POST",
            body: formData,
        });

        const data = await response.json();

        if (!response.ok) {
            errorMessage.textContent = data.detail || "Login failed";
            return;
        }

        localStorage.setItem("access_token", data.access_token);
        window.location.href = "/";
    } catch (error) {
        console.error("Login error:", error);
        errorMessage.textContent = "Something went wrong";
    }
});