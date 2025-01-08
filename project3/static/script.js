
var store = {
    topic: {},
    game: {},
};

app_pages = {
    topics: {},
    entering: {},
    searching: {},
    playing: {},
    results: {},
    disconnected: {}
};




document.addEventListener('DOMContentLoaded', function () {

    app = new Lariska({
        store: store,
        container: "#app",
        pages: app_pages,
        url: window.location.host
    });

    app.on("connect", null, () => { app.emit("get_topics") });

    app.on("topics", "#topics", (data) => { app.store.topics = data });

    app.on("game", null, (data) => {
        if (app.store.game.question_count && app.store.game.question_count != data.question_count) {
            app.run("feedback", data.feedback);
            setTimeout(() => { app.store.game = data; app.go("playing"); }, 3000);
        } else {
            app.store.game = data;
            app.go("playing");
        }
    });

    app.addHandler("feedback", (data) => {
        let answer = data.answer - 1;
        let option_element = document.querySelectorAll(".questions_option")[answer];
        option_element.classList.add("correct_option");
    });
    
    app.on("over", null, (data) => {
        app.store.over = data;
        app.go("results");
    });

    app.addHandler("back", () => { app.go("topics"); });

    app.addHandler("pick_topic", (topic) => {
        app.store.topic = topic;
        app.go("entering");
    });

    app.addHandler("join", () => {
        let playerName = document.getElementById("player_name").value;
        app.emit("join_game", { topic_pk: app.store.topic.pk, name: playerName });
        app.go("searching");
    });

    app.addHandler("answer", (index) => {
        app.emit("answer", { index: index + 1, game_uid: app.store.game.uid });
        let option_element = document.querySelectorAll(".questions_option")[index];
        option_element.classList.add("selected_option");
    });

    app.on("disconnect", "#disconnect");
});
