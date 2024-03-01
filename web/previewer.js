function cropro__play_remote_audio(element_id) {
    const element = document.getElementById(element_id);
    if (element.paused) {
        element.play();
    } else {
        element.currentTime = 0;
    }
}
