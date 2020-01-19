function updateDatepicker() {
    if (!displayDateOnly) {
        $("#date").val(formatDate(activeDate));
    }
}

function update() {
    console.log("Render new.");

    updateDatepicker();
}

function loadNew() {
    window.location.href = dest + formatDateForDjango(activeDate);
}

function onDateChanged() {
    var str = $("#date").val();
    var split = str.split(".");
    activeDate = new Date(split[2], split[1] - 1, split[0]);
    update();
    loadNew();
}


$(document).ready(function () {
    $("#date").change(onDateChanged);

    update();
});
