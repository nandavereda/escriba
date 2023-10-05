// @license magnet:?xt=urn:btih:90dc5c0be029de84e523b9b3922520e79e0e6f08&dn=cc0.txt CC0-1.0
// Modify time tags to show relative time from now
// Copyright (C) 2022-2023 Fernanda Queiroz <dev@vereda.tec.br>
dayjs.extend(window.dayjs_plugin_relativeTime);
dayjs.extend(window.dayjs_plugin_localizedFormat);
function updateTimeTag(tag) {
    let dt = dayjs(tag.dateTime).locale(navigator.language);
    tag.textContent = dt.fromNow();
    tag.title = dt.format("LLL");
}
function updateDatetime() {
    let dateTimeTags = document.querySelectorAll("time");
    for (let i=0; i<dateTimeTags.length; i++) {
        updateTimeTag(dateTimeTags[i]);
    }
}
updateDatetime();
const delay = async (ms = 1000) => new Promise(resolve => setTimeout(resolve, ms));
async function makeLoopWait() {
    while (true) {
        updateDatetime();
        await delay(30000);
    }
}
makeLoopWait();
// @license-end