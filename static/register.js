const errorMessage = document.querySelector("#errorMessage");
const registerForm = document.querySelector("#registerForm");

registerForm.addEventListener("submit", async function (event) {
    event.preventDefault();

    const username = document.querySelector("#username").value;
    const email = document.querySelector("#email").value;
    const password = document.querySelector("#password").value;
    

    const data = {
    username: username,
    email: email,
    password: password
};

console.log(data);

    const response = await fetch("/register", {
    method: "POST",
    headers: {
    "Content-Type": "application/json"
},
    body: JSON.stringify(data)
});
const result = await response.json();

if (response.ok) {
    alert("Account created successfully!");

    window.location.href = "/login-page";
} else {
    errorMessage.textContent = result.detail;
}



    console.log(response);
});