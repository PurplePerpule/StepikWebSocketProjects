var store = {
    riddle: null,
    score: 0,
};

app_pages = {
    standby: {},
    showriddle: {},
    showresult: {},
    disconnected: {}
}

document.addEventListener('DOMContentLoaded', function () {

    app = new Lariska({
        store: store,
        container: "#app",
        pages: app_pages,
        url: window.location.host
    });

    app.addHandler("next", () => {
        app.emit("next")
    })

    app.addHandler("answer", () => {
        user_answer = document.querySelector("textarea#answer").value
        app.emit("answer", {text: user_answer})
    })

    // Получена загадка с сервера
    app.on("riddle", "#showriddle", (data) => {
        console.log(data)
        app.store.riddle = data
    })

    // Получен ответ с сервера
    app.on("result", "#showanswer", (data) => {
        console.log(data)
        app.store.riddle = data
    })

    // Получен сигнал "обновлен счет" с сервера
    app.on("score", null, (data) => {
        console.log(data)
        app.store.score = data.value
    })

    // Получен сигнал "Игра завершена"
    app.on("over", "#over", (data) => {
        console.log(data)
    })

    app.go("standby");
})
