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

function onDateBeforeClick() {
    if (activeDate.getDay() === 1) {
        var minus = 3;
    } else {
        var minus = 1;
    }
    activeDate.setDate(activeDate.getDate() - minus);
    update();
    loadNew();
}

function onDateNextClick() {
    if (activeDate.getDay() === 5) {
        var plus = 3;
    } else {
        var plus = 1;
    }
    activeDate.setDate(activeDate.getDate() + plus);
    update();
    loadNew();
}

function onDateChanged() {
    var str = $("#date").val();
    var split = str.split(".")
    activeDate = new Date(split[2], split[1] - 1, split[0]);
    update();
    loadNew();
}


$(document).ready(function () {
    $("#date-before").click(onDateBeforeClick);
    $("#date-next").click(onDateNextClick);
    $("#date").change(onDateChanged);

    update();
});
