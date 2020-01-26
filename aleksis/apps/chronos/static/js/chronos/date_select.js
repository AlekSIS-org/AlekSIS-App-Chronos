var data = getJSONScript("datepicker_data");
var activeDate = new Date(data.date);

function updateDatepicker() {
    $("#date").val(formatDate(activeDate));
}

function loadNew() {
    window.location.href = data.dest + formatDateForDjango(activeDate);
}

function onDateChanged() {
    var str = $("#date").val();
    var split = str.split(".");
    activeDate = new Date(split[2], split[1] - 1, split[0]);
    updateDatepicker();
    loadNew();
}


$(document).ready(function () {
    $("#date").change(onDateChanged);

    updateDatepicker();
});
