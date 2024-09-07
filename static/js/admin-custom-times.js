// Ensure the DOM is fully loaded before executing the script
document.addEventListener('DOMContentLoaded', function () {
    // Check if DateTimeShortcuts is defined
    if (typeof DateTimeShortcuts !== 'undefined') {
        // Override the clockHours values
        DateTimeShortcuts.clockHours.default_ = [
            [gettext_noop('Now'), -1],
            [gettext_noop('Start of 1st Period'), 9],
            [gettext_noop('Start of 2nd Period'), 10.2],
            [gettext_noop('Start of Lunch'), 11.4],
            [gettext_noop('Start of 3rd Period'), 12.4],
            [gettext_noop('Start of 4th Period'), 14],
            [gettext_noop('End of School'), 15.15]
        ];
        DateTimeShortcuts.handleClockQuicklink = function (num, val) {
            let d;
            if (val === -1) {
                d = DateTimeShortcuts.now();
            } else if (!Number.isInteger(val)) {
                // If val = something like 10.2, assume it means 10:20
                let hours = Math.floor(val);
                let raw_minutes = Math.round((val - hours) * 100);
                console.log(raw_minutes)
                d = new Date(1970, 1, 1, hours, raw_minutes, 0, 0);
            }
            else {
                d = new Date(1970, 1, 1, val, 0, 0, 0);
            }
            DateTimeShortcuts.clockInputs[num].value = d.strftime(get_format('TIME_INPUT_FORMATS')[0]);
            DateTimeShortcuts.clockInputs[num].focus();
            DateTimeShortcuts.dismissClock(num);
        },
            // Reinitialize the DateTimeShortcuts to apply the new values
            DateTimeShortcuts.init();
    }
});