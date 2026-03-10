const form = document.getElementById("businessForm");
const message = document.getElementById("message");

form.addEventListener("submit", async (e) => {
    e.preventDefault();

    const data = {
        businessName: document.getElementById("businessName").value,
        ownerName: document.getElementById("ownerName").value,
        email: document.getElementById("email").value,
        tel: document.getElementById("phoneNumber").value,
        password: document.getElementById("password").value,
        confirmPassword: document.getElementById("confirmPassword").value,
        businessType: document.getElementById("businessType").value,
        terms: document.getElementById("terms").checked,
        newsletter: document.getElementById("newsletter").checked
    };

    try {
        const response = await fetch("/api/business/register", {
            method: "POST",
            headers: {
                "Content-Type": "application/json" },
                body: JSON.stringify(data)
        });

        const result = await response.json();

        if (!response.ok) {
            message.style.color = "red";
            message.textContent = result.message;
        } else {
            message.style.color = "green";
            message.textContent = result.message;
            form.reset();
        }
    } catch (error) {
        message.style.color = "red";
        message.textContent = "An error occurred. Please try again later.";
    }
});