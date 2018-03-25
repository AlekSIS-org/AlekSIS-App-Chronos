class Lesson(object):
    def __init__(self):
        self.filled = False
        self.id = None
        self.elements = []
        self.times = []

    def add_element(self, teacher, subject, rooms=[], classes=[]):
        el = LessonElement()
        el.create(teacher, subject, rooms, classes)
        self.elements.append(el)

    def add_time(self, day, hour, rooms=[]):
        el = LessonTime()
        el.create(day, hour, rooms)
        self.times.append(el)

    def create(self, db_obj):
        self.filled = True


class LessonElement(object):
    def __init__(self):
        self.teacher = None
        self.subject = None
        self.rooms = []
        self.classes = []

    def create(self, teacher, subject, rooms=[], classes=[]):
        self.teacher = teacher
        self.subject = subject
        self.rooms = rooms
        self.classes = classes


class LessonTime(object):
    def __init__(self):
        self.hour = None
        self.day = None
        self.rooms = []

    def create(self, day, hour, rooms=[]):
        self.day = day
        self.hour = hour
        self.rooms = rooms


from untisconnect.api import *

try:
    from schoolapps.untisconnect.api import *
except Exception:
    pass


def clean_array(a, conv=None):
    b = []
    for el in a:
        if el != '' and el != "0":
            if conv is not None:
                el = conv(el)
            b.append(el)
    return b


def untis_split(s, conv=None):
    return clean_array(s.split(";"), conv=conv)


def parse():
    odrive = {
        "teachers": get_all_teachers(),
        "rooms": get_all_rooms(),
        "classes": get_all_classes(),
        "subjects": get_all_subjects()
    }

    drive = {
        "teachers": {},
        "rooms": {},
        "classes": {},
        "subjects": {}
    }
    for key, value in odrive.items():
        for el in value:
            id = el.id
            drive[key][id] = el

    print(drive)

    lessons = []
    raw_lessons = get_raw_lessons()

    for raw_lesson in raw_lessons:
        # print("[RAW LESSON]")
        # print("LESSON_ID      | ", raw_lesson.lesson_id)
        # print("LessonElement1 | ", raw_lesson.lessonelement1)
        # print("Lesson_TT      | ", raw_lesson.lesson_tt)

        if raw_lesson.lesson_tt and raw_lesson.lessonelement1:
            # Create object
            lesson_obj = Lesson()

            # Split data (,)
            lesson_id = raw_lesson.lesson_id
            raw_lesson_data = raw_lesson.lessonelement1.split(",")
            raw_time_data = raw_lesson.lesson_tt.split(",")

            # print(raw_lesson_data)
            # print(raw_time_data)

            # Split data more (~)
            rld2 = []
            for el in raw_lesson_data:
                rld2.append(el.split("~"))

            # print(rld2)

            for el in rld2:
                teacher_id = int(el[0])
                subject_id = int(el[2])
                room_ids = untis_split(el[4], int)
                class_ids = untis_split(el[17], conv=int)
                # print("TEACHER – ", teacher_id, "; SUBJECT – ", subject_id, "; ROOMS – ", room_ids, "; CLASSES – ",
                #       class_ids)

                if teacher_id != 0:
                    teacher = drive["teachers"][teacher_id]
                else:
                    teacher = None

                if subject_id != 0:
                    subject = drive["subjects"][subject_id]
                else:
                    subject = None

                rooms = []
                for room_id in room_ids:
                    r = drive["rooms"][room_id]
                    rooms.append(r)

                classes = []
                for class_id in class_ids:
                    c = drive["classes"][class_id]
                    classes.append(c)

                # print("TEACHER – ", teacher, "; SUBJECT – ", subject, "; ROOMS – ", rooms,
                #       "; CLASSES – ", classes)

                lesson_obj.add_element(teacher, subject, rooms, classes)

            rtd2 = []
            for el in raw_time_data:
                rtd2.append(el.split("~"))

            # print(rtd2)

            for el in rtd2:
                day = int(el[1])
                hour = int(el[2])
                room_ids = untis_split(el[3], conv=int)

                rooms = []
                for room_id in room_ids:
                    r = drive["rooms"][room_id]
                    rooms.append(r)

                lesson_obj.add_time(day, hour, rooms)

                # print("DAY – ", day, "; HOUR – ", hour, "; ROOMS – ", room_ids)

            lessons.append(lesson_obj)

    return lessons


TYPE_TEACHER = 0
TYPE_ROOM = 1
TYPE_CLASS = 2


def get_plan(type, id):
    lessons = parse()
    plan = [[[], [], [], [], []],
            [[], [], [], [], []],
            [[], [], [], [], []],
            [[], [], [], [], []],
            [[], [], [], [], []],
            [[], [], [], [], []],
            [[], [], [], [], []],
            [[], [], [], [], []],
            [[], [], [], [], []],
            [[], [], [], [], []],
            [[], [], [], [], []]]

    for lesson in lessons:
        for element in lesson.elements:
            found = False
            if type == TYPE_CLASS:
                for lclass in element.classes:
                    if lclass.id == id:
                        found = True

            elif type == TYPE_TEACHER:
                if element.teacher:
                    if element.teacher.id == id:
                        found = True

            elif type == TYPE_ROOM:
                for lroom in element.rooms:
                    if lroom.id == id:
                        found = True

            if found:
                for time in lesson.times:
                    # print(time.hour, " ", time.day)
                    # print(element.subject.shortcode)
                    plan[time.hour - 1][time.day - 1].append(element)

    # print(plan)

    return plan
