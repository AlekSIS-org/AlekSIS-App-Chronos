var data = getJSONScript("week_select");

function goToCalendarWeek(cw, year) {
    window.location.href = data.dest.replace("year", year).replace("cw", cw);
}

function onCalendarWeekChanged(where) {
    goToCalendarWeek($(where).val(), data.year);
}

$(document).ready(function () {
    $("#calendar-week-1").change(function () {
        onCalendarWeekChanged("#calendar-week-1");
    });
    $("#calendar-week-2").change(function () {
        onCalendarWeekChanged("#calendar-week-2");
    });
    $("#calendar-week-3").change(function () {
        onCalendarWeekChanged("#calendar-week-3");
    });
});
