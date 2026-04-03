async function sendMessage() {
    let msgInput = document.getElementById("msg");
    let chatBox = document.getElementById("chatBox");

    let message = msgInput.value;
    if (!message) return;

    chatBox.innerHTML += `<p><b>You:</b> ${message}</p>`;
    msgInput.value = "";

    try {
        let res = await fetch("/chat", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ message: message })
        });

        let data = await res.json();

        chatBox.innerHTML += `<p><b>AI:</b> ${data.reply}</p>`;
    } catch (err) {
        chatBox.innerHTML += `<p style="color:red;">Error connecting</p>`;
    }

    chatBox.scrollTop = chatBox.scrollHeight;
}