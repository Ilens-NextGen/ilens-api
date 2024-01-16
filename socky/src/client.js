import io from "socket.io-client";
import $ from "jquery";


const client = io("https://8000-ilensnextgen-ilensapi-miwg4r44eqe.ws-eu107.gitpod.io", {
    transports: ["websocket", "polling", "flashsocket"]
});

client.on("connect", () => {
    console.log("connected");
})

client.on("disconnect", () => {
    console.log("disconnected");
})

client.on("response", (data) => {
    console.log("response", data);
})
client.on('ai_reply', (data) => {
    let result = data;
    console.log("result", result);
    $("#chat-log").append(`<li class='ai'>${result}</li>`);
});
client.on('result', data => {
    console.log("Gotten", data);
})
export default client;