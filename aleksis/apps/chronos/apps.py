from aleksis.core.util.apps import AppConfig


class ChronosConfig(AppConfig):
    name = "aleksis.apps.chronos"
    verbose_name = "AlekSIS — Chronos (Timetables)"

    urls = {
        "Repository": "https://edugit.org/AlekSIS/official/AlekSIS-App-Chronos/",
    }
    licence = "EUPL-1.2+"
    copyright_info = (
        ([2018, 2019, 2020], "Jonathan Weth", "wethjo@katharineum.de"),
        ([2018, 2019], "Frank Poetzsch-Heffter", "p-h@katharineum.de"),
        ([2019, 2020], "Dominik George", "dominik.george@teckids.org"),
        ([2019], "Julian Leucker", "leuckeju@katharineum.de"),
        ([2019], "Tom Teichler", "tom.teichler@teckids.org"),
        ([2019], "Hangzhi Yu", "yuha@katharineum.de"),
    )
