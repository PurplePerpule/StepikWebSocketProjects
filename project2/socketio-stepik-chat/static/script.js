var store = {
    messages: [],
    rooms: ["lobby", "hobby", "bobby"],
    error: null,
    message: ""
};

app_pages = {
    selectroom: {},
    createroom: {},
    chat: {}
}

document.addEventListener('DOMContentLoaded', function () {

    app = new Lariska({
        store: store,
        container: "#app",
        pages: app_pages,
        url: window.location.host
    });

    app.addHandler("join", () => {
        user_room = document.getElementById("user_room").value
        user_name = document.getElementById("user_name").value
        app.emit("join", {name: user_name, room: user_room})
    })

    app.addHandler("send", () => {
        user_input = document.getElementById("user_message")
        user_message = user_input.value
        user_input.value = ""
        app.emit("send_message", {text: user_message})
    })

    app.addHandler("back", () => {
        app.emit("leave")
        app.store.messages = []
        app.go("selectroom")
    })

    app.on("connect", null, () => {
        app.emit("get_rooms")
    })

    app.on("disconnect", "#disconnect")

    app.on("rooms", "#selectroom", (data) => {
        app.store.rooms = data
    })

    app.on("move", "#chat", (data) => {
        app.store.room = data.room
    })

    app.on("message", "#messages", (data) => {
        app.store.messages.push(data)
    }, ".chat-messages")

})
