TIMETABLE_FORMATS = {  # possible formats for timetables, position is the classes it can hold in day one and day two format.
    "pre-2020": {
        "schedules": {
            "default": [
                {
                    "description": {
                        "time": "08:45 am - 10:05 am",
                        "course": "Period 1",
                    },
                    "time": [[8, 45], [10, 5]],
                    "position": [{1}, {1}],
                },
                {
                    "description": {
                        "time": "10:15 am - 11:30 am",
                        "course": "Period 2",
                    },
                    "time": [[10, 15], [11, 30]],
                    "position": [{2}, {2}],
                },
                {
                    "description": {
                        "time": "12:30 pm - 01:45 pm",
                        "course": "Period 3",
                    },
                    "time": [[12, 30], [13, 45]],
                    "position": [{3}, {4}],
                },
                {
                    "description": {
                        "time": "01:50 pm - 03:05 pm",
                        "course": "Period 4",
                    },
                    "time": [[13, 50], [15, 5]],
                    "position": [{4}, {3}],
                },
            ]
        },
        "courses": 4,
        "positions": {1, 2, 3, 4},
        "cycle": {
            "length": 2,
            "duration": "day",
        },
        "question": {
            "prompt": "Your Nth course on day 1 is this course. N = ?",
            "choices": [
                (1, 1),
                (2, 2),
                (3, 3),
                (4, 4),
            ],
        },
    },
    "covid": {
        "schedules": {
            "default": [
                {
                    "description": {
                        "time": "08:45 am - 12:30 pm (In person)",
                        "course": "Morning Class",
                    },
                    "time": [[8, 45], [12, 30]],
                    "position": [{1}, {2}, {3}, {4}],
                },
                {
                    "description": {
                        "time": "08:45 am - 12:30 pm (At home)",
                        "course": "Morning Class",
                    },
                    "time": [[8, 45], [12, 30]],
                    "position": [{2}, {1}, {4}, {3}],
                },
                {
                    "description": {
                        "time": "02:00 pm - 03:15 pm (At home)",
                        "course": "Afternoon Class",
                    },
                    "time": [[14, 0], [15, 15]],
                    "position": [{3, 4}, {3, 4}, {1, 2}, {1, 2}],
                },
            ],
        },
        "courses": 2,
        "positions": {1, 2, 3, 4},
        "cycle": {
            "length": 4,
            "duration": "day",
        },
        "question": {
            "prompt": "On which day are you in person for this course?",
            "choices": [
                (1, 1),
                (2, 2),
                (3, 3),
                (4, 4),
            ],
        },
    },
    "week": {
        "schedules": {
            "default": [
                {
                    "description": {
                        "time": "09:00 am - 11:30 am",
                        "course": "Morning Class",
                    },
                    "time": [[9, 0], [11, 30]],
                    "position": [{1, 5, 7}, {3, 6, 7}],
                },
                {
                    "description": {
                        "time": "12:15 pm - 02:45 pm",
                        "course": "Afternoon Class",
                    },
                    "time": [[12, 15], [14, 45]],
                    "position": [{2, 5, 7}, {4, 6, 7}],
                },
            ],
            "late-start": [
                {
                    "description": {
                        "time": "10:00 am - 12:00 pm",
                        "course": "Morning Class",
                    },
                    "time": [[10, 0], [12, 0]],
                    "position": [{1, 5, 7}, {3, 6, 7}],
                },
                {
                    "description": {
                        "time": "12:45 pm - 02:45 pm",
                        "course": "Afternoon Class",
                    },
                    "time": [[12, 45], [14, 45]],
                    "position": [{2, 5, 7}, {4, 6, 7}],
                },
            ],
            "early-dismissal": [
                {
                    "description": {
                        "time": "09:00 am - 10:14 am",
                        "course": "Morning Class",
                    },
                    "time": [[9, 0], [10, 14]],
                    "position": [{1, 5, 7}, {3, 6, 7}],
                },
                {
                    "description": {
                        "time": "10:16 am - 11:30 am",
                        "course": "Afternoon Class",
                    },
                    "time": [[10, 16], [11, 30]],
                    "position": [{2, 5, 7}, {4, 6, 7}],
                },
            ],
            "early-early-dismissal": [
                {
                    "description": {
                        "time": "09:00 am - 9:55 am",
                        "course": "1st Classes",
                    },
                    "time": [[9, 0], [9, 55]],
                    "position": [{1, 5, 7}, {3, 6, 7}],
                },
                {
                    "description": {
                        "time": "10:00 am - 11:00 am",
                        "course": "2nd Classes",
                    },
                    "time": [[10, 0], [11, 0]],
                    "position": [{2, 5, 7}, {4, 6, 7}],
                },
            ],
        },
        "courses": 4,
        "positions": {1, 2, 3, 4, 5, 6, 7},
        "cycle": {
            "length": 2,
            "duration": "week",
        },
        "question": {
            "prompt": "When do you have class for this course?",
            "choices": [
                (1, "Week 1 Morning"),
                (2, "Week 1 Afternoon"),
                (3, "Week 2 Morning"),
                (4, "Week 2 Afternoon"),
                (5, "This course is a 2-credit Co-op in Week 1."),
                (6, "This course is a 2-credit Co-op in Week 2."),
                (7, "This course is a 4-credit Co-op."),
            ],
        },
    },
    "post-covid": {
        "schedules": {
            "default": [
                {
                    "description": {
                        "time": "09:00 am - 10:15 am",
                        "course": "Period 1",
                    },
                    "time": [[9, 00], [10, 15]],
                    "position": [{1, 5}, {1, 5}],
                },
                {
                    "description": {
                        "time": "10:20 am - 11:35 am",
                        "course": "Period 2",
                    },
                    "time": [[10, 20], [11, 35]],
                    "position": [{2, 5}, {2, 5}],
                },
                {
                    "description": {
                        "time": "12:20 pm - 01:35 pm",
                        "course": "Period 3",
                    },
                    "time": [[12, 20], [13, 35]],
                    "position": [{3, 6}, {4, 6}],
                },
                {
                    "description": {
                        "time": "01:40 pm - 02:55 pm",
                        "course": "Period 4",
                    },
                    "time": [[13, 40], [14, 55]],
                    "position": [{4, 6}, {3, 6}],
                },
            ],
            "late-start": [
                {
                    "description": {
                        "time": "10:00 am - 11:00 am",
                        "course": "Period 1",
                    },
                    "time": [[10, 0], [11, 0]],
                    "position": [{1, 5}, {1, 5}],
                },
                {
                    "description": {
                        "time": "11:05 am - 12:05 am",
                        "course": "Period 2",
                    },
                    "time": [[11, 5], [12, 5]],
                    "position": [{2, 5}, {2, 5}],
                },
                {
                    "description": {
                        "time": "12:50 pm - 01:50 pm",
                        "course": "Period 3",
                    },
                    "time": [[12, 50], [13, 50]],
                    "position": [{3, 6}, {4, 6}],
                },
                {
                    "description": {
                        "time": "01:55 pm - 02:55 pm",
                        "course": "Period 4",
                    },
                    "time": [[13, 55], [14, 55]],
                    "position": [{4, 6}, {3, 6}],
                },
            ],
            "early-dismissal": [
                {
                    "description": {
                        "time": "09:00 am - 09:45 am",
                        "course": "Period 1",
                    },
                    "time": [[9, 0], [9, 45]],
                    "position": [{1, 5}, {1, 5}],
                },
                {
                    "description": {
                        "time": "09:50 am - 10:30 am",
                        "course": "Period 2",
                    },
                    "time": [[9, 50], [10, 30]],
                    "position": [{2, 5}, {2, 5}],
                },
                {
                    "description": {
                        "time": "10:35 am - 11:15 am",
                        "course": "Period 3",
                    },
                    "time": [[10, 35], [11, 15]],
                    "position": [{3, 6}, {4, 6}],
                },
                {
                    "description": {
                        "time": "11:20 am - 12:00 pm",
                        "course": "Period 4",
                    },
                    "time": [[11, 20], [12, 0]],
                    "position": [{4, 6}, {3, 6}],
                },
            ],
            "one-hour-lunch": [
                {
                    "description": {
                        "time": "09:00 am - 10:15 am",
                        "course": "Period 1",
                    },
                    "time": [[9, 00], [10, 15]],
                    "position": [{1, 5}, {1, 5}],
                },
                {
                    "description": {
                        "time": "10:20 am - 11:30 am",
                        "course": "Period 2",
                    },
                    "time": [[10, 20], [11, 30]],
                    "position": [{2, 5}, {2, 5}],
                },
                {
                    "description": {
                        "time": "12:30 pm - 01:40 pm",
                        "course": "Period 3",
                    },
                    "time": [[12, 30], [13, 40]],
                    "position": [{3, 6}, {4, 6}],
                },
                {
                    "description": {
                        "time": "01:45 pm - 02:55 pm",
                        "course": "Period 4",
                    },
                    "time": [[13, 45], [14, 55]],
                    "position": [{4, 6}, {3, 6}],
                },
            ],
            "early-early-dismissal": [
                {
                    "description": {
                        "time": "09:00 am - 09:25 am",
                        "course": "Period 1",
                    },
                    "time": [[9, 0], [9, 25]],
                    "position": [{1, 5}, {1, 5}],
                },
                {
                    "description": {
                        "time": "09:30 am - 9:55 am",
                        "course": "Period 2",
                    },
                    "time": [[9, 30], [9, 55]],
                    "position": [{2, 5}, {2, 5}],
                },
                {
                    "description": {
                        "time": "10:00 am - 10:25 am",
                        "course": "Period 3",
                    },
                    "time": [[10, 0], [10, 25]],
                    "position": [{3, 6}, {4, 6}],
                },
                {
                    "description": {
                        "time": "10:30 am - 11:00 am",
                        "course": "Period 4",
                    },
                    "time": [[10, 30], [11, 0]],
                    "position": [{4, 6}, {3, 6}],
                },
            ],
        },
        "courses": 4,
        "positions": {1, 2, 3, 4, 5, 6},
        "cycle": {
            "length": 2,
            "duration": "day",
        },
        "question": {
            "prompt": "On Day 1, which period is this course in?",
            "choices": [
                (1, "Period 1"),
                (2, "Period 2"),
                (3, "Period 3"),
                (4, "Period 4"),
                (5, "This course is a 2-credit Co-op in the morning."),
                (6, "This course is a 2-credit Co-op in the afternoon."),
            ],
        },
    },
    "2022-2023": {
        "day_num_method": "calendar_days",
        "schedules": {
            "default": [
                {
                    "description": {
                        "time": "09:00 am - 10:20 am",
                        "course": "Period 1",
                    },
                    "time": [[9, 0], [10, 20]],
                    "position": [{1, 5}, {1, 5}],
                },
                {
                    "description": {
                        "time": "10:25 am - 11:40 am",
                        "course": "Period 2",
                    },
                    "time": [[10, 25], [11, 40]],
                    "position": [{2, 5}, {2, 5}],
                },
                {
                    "description": {
                        "time": "12:40 pm - 01:55 pm",
                        "course": "Period 3",
                    },
                    "time": [[12, 40], [13, 55]],
                    "position": [{3, 6}, {4, 6}],
                },
                {
                    "description": {
                        "time": "02:00 pm - 03:15 pm",
                        "course": "Period 4",
                    },
                    "time": [[14, 0], [15, 15]],
                    "position": [{4, 6}, {3, 6}],
                },
            ],
            "late-start": [
                {
                    "description": {
                        "time": "10:00 am - 11:05 am",
                        "course": "Period 1",
                    },
                    "time": [[10, 0], [11, 5]],
                    "position": [{1, 5}, {1, 5}],
                },
                {
                    "description": {
                        "time": "11:10 am - 12:10 pm",
                        "course": "Period 2",
                    },
                    "time": [[11, 10], [12, 10]],
                    "position": [{2, 5}, {2, 5}],
                },
                {
                    "description": {
                        "time": "01:10 pm - 02:10 pm",
                        "course": "Period 3",
                    },
                    "time": [[13, 10], [14, 10]],
                    "position": [{3, 6}, {4, 6}],
                },
                {
                    "description": {
                        "time": "02:15 pm - 03:15 pm",
                        "course": "Period 4",
                    },
                    "time": [[14, 15], [15, 15]],
                    "position": [{4, 6}, {3, 6}],
                },
            ],
            "half-day": [
                {
                    "description": {
                        "time": "09:00 am - 09:45 am",
                        "course": "Period 1",
                    },
                    "time": [[9, 0], [9, 45]],
                    "position": [{1, 5}, {1, 5}],
                },
                {
                    "description": {
                        "time": "09:50 am - 10:35 pm",
                        "course": "Period 2",
                    },
                    "time": [[9, 50], [10, 35]],
                    "position": [{2, 5}, {2, 5}],
                },
                {
                    "description": {
                        "time": "10:40 pm - 11:25 pm",
                        "course": "Period 3",
                    },
                    "time": [[10, 40], [11, 25]],
                    "position": [{3, 6}, {4, 6}],
                },
                {
                    "description": {
                        "time": "11:30 pm - 12:15 pm",
                        "course": "Period 4",
                    },
                    "time": [[11, 30], [12, 15]],
                    "position": [{4, 6}, {3, 6}],
                },
            ],
            "sac-election": [
                {
                    "description": {
                        "time": "09:00 am - 10:40 am",
                        "course": "Period 1",
                    },
                    "time": [[9, 0], [10, 40]],
                    "position": [{1, 5}, {1, 5}],
                },
                {
                    "description": {
                        "time": "10:45 am - 12:10 pm",
                        "course": "Period 2",
                    },
                    "time": [[10, 45], [12, 10]],
                    "position": [{2, 5}, {2, 5}],
                },
                {
                    "description": {
                        "time": "01:10 pm - 02:10 pm",
                        "course": "Period 3",
                    },
                    "time": [[13, 10], [14, 10]],
                    "position": [{3, 6}, {4, 6}],
                },
                {
                    "description": {
                        "time": "02:15 pm - 03:15 pm",
                        "course": "Period 4",
                    },
                    "time": [[14, 15], [15, 15]],
                    "position": [{4, 6}, {3, 6}],
                },
            ],
        },
        "courses": 4,
        "positions": {1, 2, 3, 4, 5, 6},
        "cycle": {
            "length": 2,
            "duration": "day",
        },
        "question": {
            "prompt": "On Day 1, which period is this course in?",
            "choices": [
                (1, "Period 1"),
                (2, "Period 2"),
                (3, "Period 3"),
                (4, "Period 4"),
                (5, "This course is a 2-credit Co-op in the morning."),
                (6, "This course is a 2-credit Co-op in the afternoon."),
            ],
        },
    },
    "2023-2024": {
        "day_num_method": "calendar_days",
        "schedules": {
            "default": [
                {
                    "description": {
                        "time": "09:00 am - 10:20 am",
                        "course": "Period 1",
                    },
                    "time": [[9, 0], [10, 20]],
                    "position": [{1, 5}, {1, 5}],
                },
                {
                    "description": {
                        "time": "10:25 am - 11:40 am",
                        "course": "Period 2",
                    },
                    "time": [[10, 25], [11, 40]],
                    "position": [{2, 5}, {2, 5}],
                },
                {
                    "description": {
                        "time": "12:40 pm - 01:55 pm",
                        "course": "Period 3",
                    },
                    "time": [[12, 40], [13, 55]],
                    "position": [{3, 6}, {4, 6}],
                },
                {
                    "description": {
                        "time": "02:00 pm - 03:15 pm",
                        "course": "Period 4",
                    },
                    "time": [[14, 0], [15, 15]],
                    "position": [{4, 6}, {3, 6}],
                },
            ],
            "late-start": [
                {
                    "description": {
                        "time": "9:55 am - 10:55 am",  # todo check if this should be 10 or 9:55
                        "course": "Period 1",
                    },
                    "time": [[9, 55], [10, 55]],
                    "position": [{1, 5}, {1, 5}],
                },
                {
                    "description": {
                        "time": "11:00 am - 12:00 pm",
                        "course": "Period 2",
                    },
                    "time": [[11, 0], [12, 0]],
                    "position": [{2, 5}, {2, 5}],
                },
                {
                    "description": {
                        "time": "01:05 pm - 02:10 pm",  # todo check if this should be 1:10 or 1:05
                        "course": "Period 3",
                    },
                    "time": [[13, 5], [14, 10]],
                    "position": [{3, 6}, {4, 6}],
                },
                {
                    "description": {
                        "time": "02:15 pm - 03:15 pm",
                        "course": "Period 4",
                    },
                    "time": [[14, 15], [15, 15]],
                    "position": [{4, 6}, {3, 6}],
                },
            ],
            "half-day": [
                {
                    "description": {
                        "time": "09:00 am - 09:45 am",
                        "course": "Period 1",
                    },
                    "time": [[9, 0], [9, 45]],
                    "position": [{1, 5}, {1, 5}],
                },
                {
                    "description": {
                        "time": "09:50 am - 10:35 pm",
                        "course": "Period 2",
                    },
                    "time": [[9, 50], [10, 35]],
                    "position": [{2, 5}, {2, 5}],
                },
                {
                    "description": {
                        "time": "10:40 pm - 11:25 pm",
                        "course": "Period 3",
                    },
                    "time": [[10, 40], [11, 25]],
                    "position": [{3, 6}, {4, 6}],
                },
                {
                    "description": {
                        "time": "11:30 pm - 12:15 pm",
                        "course": "Period 4",
                    },
                    "time": [[11, 30], [12, 15]],
                    "position": [{4, 6}, {3, 6}],
                },
            ],
            "sac-election": [
                {
                    "description": {
                        "time": "09:00 am - 10:40 am",
                        "course": "Period 1",
                    },
                    "time": [[9, 0], [10, 40]],
                    "position": [{1, 5}, {1, 5}],
                },
                {
                    "description": {
                        "time": "10:45 am - 12:10 pm",
                        "course": "Period 2",
                    },
                    "time": [[10, 45], [12, 10]],
                    "position": [{2, 5}, {2, 5}],
                },
                {
                    "description": {
                        "time": "01:10 pm - 02:10 pm",
                        "course": "Period 3",
                    },
                    "time": [[13, 10], [14, 10]],
                    "position": [{3, 6}, {4, 6}],
                },
                {
                    "description": {
                        "time": "02:15 pm - 03:15 pm",
                        "course": "Period 4",
                    },
                    "time": [[14, 15], [15, 15]],
                    "position": [{4, 6}, {3, 6}],
                },
            ],
        },
        "courses": 4,
        "positions": {1, 2, 3, 4, 5, 6},
        "cycle": {
            "length": 2,
            "duration": "day",
        },
        "question": {
            "prompt": "On Day 1, which period is this course in?",
            "choices": [
                (1, "Period 1"),
                (2, "Period 2"),
                (3, "Period 3"),
                (4, "Period 4"),
                (5, "This course is a 2-credit Co-op in the morning."),
                (6, "This course is a 2-credit Co-op in the afternoon."),
            ],
        },
    },
    "2024-2025": {
        "day_num_method": "calendar_days",
        "schedules": {
            "default": [
                {
                    "description": {
                        "time": "09:00 am - 10:20 am",
                        "course": "Period 1",
                    },
                    "time": [[9, 0], [10, 20]],
                    "position": [{1, 5}, {1, 5}],
                },
                {
                    "description": {
                        "time": "10:25 am - 11:40 am",
                        "course": "Period 2",
                    },
                    "time": [[10, 25], [11, 40]],
                    "position": [{2, 5}, {2, 5}],
                },
                {
                    "description": {
                        "time": "12:40 pm - 01:55 pm",
                        "course": "Period 3",
                    },
                    "time": [[12, 40], [13, 55]],
                    "position": [{3, 6}, {4, 6}],
                },
                {
                    "description": {
                        "time": "02:00 pm - 03:15 pm",
                        "course": "Period 4",
                    },
                    "time": [[14, 0], [15, 15]],
                    "position": [{4, 6}, {3, 6}],
                },
            ],
            "late-start": [
                {
                    "description": {
                        "time": "9:55 am - 10:55 am",  # todo check if this should be 10 or 9:55
                        "course": "Period 1",
                    },
                    "time": [[9, 55], [10, 55]],
                    "position": [{1, 5}, {1, 5}],
                },
                {
                    "description": {
                        "time": "11:00 am - 12:00 pm",
                        "course": "Period 2",
                    },
                    "time": [[11, 0], [12, 0]],
                    "position": [{2, 5}, {2, 5}],
                },
                {
                    "description": {
                        "time": "01:05 pm - 02:10 pm",  # todo check if this should be 1:10 or 1:05
                        "course": "Period 3",
                    },
                    "time": [[13, 5], [14, 10]],
                    "position": [{3, 6}, {4, 6}],
                },
                {
                    "description": {
                        "time": "02:15 pm - 03:15 pm",
                        "course": "Period 4",
                    },
                    "time": [[14, 15], [15, 15]],
                    "position": [{4, 6}, {3, 6}],
                },
            ],
            "half-day": [
                {
                    "description": {
                        "time": "09:00 am - 09:45 am",
                        "course": "Period 1",
                    },
                    "time": [[9, 0], [9, 45]],
                    "position": [{1, 5}, {1, 5}],
                },
                {
                    "description": {
                        "time": "09:50 am - 10:35 pm",
                        "course": "Period 2",
                    },
                    "time": [[9, 50], [10, 35]],
                    "position": [{2, 5}, {2, 5}],
                },
                {
                    "description": {
                        "time": "10:40 pm - 11:25 pm",
                        "course": "Period 3",
                    },
                    "time": [[10, 40], [11, 25]],
                    "position": [{3, 6}, {4, 6}],
                },
                {
                    "description": {
                        "time": "11:30 pm - 12:15 pm",
                        "course": "Period 4",
                    },
                    "time": [[11, 30], [12, 15]],
                    "position": [{4, 6}, {3, 6}],
                },
            ],
            "sac-election": [
                {
                    "description": {
                        "time": "09:00 am - 10:40 am",
                        "course": "Period 1",
                    },
                    "time": [[9, 0], [10, 40]],
                    "position": [{1, 5}, {1, 5}],
                },
                {
                    "description": {
                        "time": "10:45 am - 12:10 pm",
                        "course": "Period 2",
                    },
                    "time": [[10, 45], [12, 10]],
                    "position": [{2, 5}, {2, 5}],
                },
                {
                    "description": {
                        "time": "01:10 pm - 02:10 pm",
                        "course": "Period 3",
                    },
                    "time": [[13, 10], [14, 10]],
                    "position": [{3, 6}, {4, 6}],
                },
                {
                    "description": {
                        "time": "02:15 pm - 03:15 pm",
                        "course": "Period 4",
                    },
                    "time": [[14, 15], [15, 15]],
                    "position": [{4, 6}, {3, 6}],
                },
            ],
        },
        "courses": 4,
        "positions": {1, 2, 3, 4, 5, 6},
        "cycle": {
            "length": 2,
            "duration": "day",
        },
        "question": {
            "prompt": "On Day 1, which period is this course in?",
            "choices": [
                (1, "Period 1"),
                (2, "Period 2"),
                (3, "Period 3"),
                (4, "Period 4"),
                (5, "This course is a 2-credit Co-op in the morning."),
                (6, "This course is a 2-credit Co-op in the afternoon."),
            ],
        },
    },
}
