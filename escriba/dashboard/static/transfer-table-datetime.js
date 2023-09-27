// @license magnet:?xt=urn:btih:90dc5c0be029de84e523b9b3922520e79e0e6f08&dn=cc0.txt CC0-1.0
// Modify datetime column to show relative time from now
// Copyright (C) 2022-2023 Fernanda Queiroz <dev@vereda.tec.br>
dayjs.extend(window.dayjs_plugin_relativeTime);
dayjs.extend(window.dayjs_plugin_localizedFormat);
const dateIdx = 1;
const trs = document.querySelector("#transfer-table").getElementsByTagName("tr");
function updateDatetimeText() {
    for (var i=1; i<trs.length; i++) {
        var dateTimeCell = trs[i].children[dateIdx].firstChild;
        var dt = dayjs(dateTimeCell.dateTime).locale(navigator.language);
        dateTimeCell.textContent = dt.fromNow();
        dateTimeCell.title = dt.format("LLL");
    }
}
const delay = async (ms = 1000) => new Promise(resolve => setTimeout(resolve, ms));
updateDatetimeText();
async function makeLoopWait() {
    while (true) {
        updateDatetimeText();
        await delay(30000);
    }
 }
 makeLoopWait();
// @license-end