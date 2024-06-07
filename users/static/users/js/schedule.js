$(document).ready(function() {
    var calendar = $('#calendar').fullCalendar({
        header: {
            left: 'prev,next today',
            center: 'title',
            right: 'month,agendaWeek,agendaDay'
        },
        defaultView: 'month',
        defaultDate: moment().format('YYYY-MM-DD'),
        navLinks: true,
        selectable: true,
        selectHelper: true,
        editable: true,
        events: function(start, end, timezone, callback) {
            // Fetch events with start and end dates
            fetch(staffScheduleUrl + `?start=${start.format('YYYY-MM-DD')}&end=${end.format('YYYY-MM-DD')}`)
                .then(response => response.json())
                .then(data => {
                    callback(data.events);
                    updateAlwaysOffDays(data.alwaysOffDays);
                    updateDaysOffList();
                });
        },
        eventAfterAllRender: function(view) {
            updateDaysOffList();
        },
        select: function(start, end) {
            var date = start.format('YYYY-MM-DD');
            if (!$('#calendar').fullCalendar('clientEvents', function(evt) {
                return evt.start.format('YYYY-MM-DD') === date && evt.rendering === 'background';
            }).length) {
                if (confirm("Mark " + date + " as a day off?")) {
                    markDayAsOff(date, false);
                }
            }
            $('#calendar').fullCalendar('unselect');
        },
        eventClick: function(calEvent, jsEvent, view) {
            if (calEvent.rendering === 'background' && confirm("Remove this day off?")) {
                markDayAsOff(calEvent.start.format('YYYY-MM-DD'), true);
            }
        },
        eventRender: function(event, element) {
            if (event.rendering === 'background') {
                element.css({
                    'background-color': event.color,
                    'opacity': 0.5,
                    'border': 'none'
                });
            }
        }
    });

    function updateAlwaysOffDays(alwaysOffDays) {
        var alwaysOffDaysList = document.getElementById('alwaysOffDays');
        alwaysOffDaysList.innerHTML = ''; // Clear any existing content
        alwaysOffDays.forEach(function(day) {
            var li = document.createElement('li');
            li.textContent = day;
            alwaysOffDaysList.appendChild(li);
        });
    }

    function updateDaysOffList() {
        $('#daysOffList tr:not(:first)').remove();  // Clear existing entries except the header
        var events = $('#calendar').fullCalendar('clientEvents', function(evt) {
            return evt.rendering === 'background' && evt.type === 'day_off';
        });
        events.forEach(function(evt) {
            var date = moment(evt.start);
            $('#daysOffList').append(
                '<tr><td>' + date.format('YYYY-MM-DD') + '</td>' +
                '<td>' + date.format('dddd') + '</td>' +
                '<td><button class="remove-day-off" data-date="' + date.format('YYYY-MM-DD') + '">Clear</button></td></tr>'
            );
        });
    }

    function markDayAsOff(date, available) {
        $.ajax({
            url: `/users/update_specific_date_availability/${userId}/`,
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({
                date: date,
                available: available
            }),
            beforeSend: function(xhr) {
                xhr.setRequestHeader("X-CSRFToken", getCSRFToken());
            },
            success: function(response) {
                if(response.status === 'success') {
                    alert('Day off updated successfully!');
                    calendar.fullCalendar('refetchEvents');
                    updateDaysOffList();
                } else {
                    alert('Error: ' + response.message);
                }
            },
            error: function(xhr, status, error) {
                alert("Error updating day off: " + status + " - " + error);
            }
        });
    }

    $(document).on('click', '.remove-day-off', function() {
        var date = $(this).data('date');
        if (confirm("Are you sure you want to clear the day off for " + date + "?")) {
            markDayAsOff(date, true);
        }
    });

    function getCSRFToken() {
        let csrfToken = null;
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            const cookiePair = cookie.split('=');
            if (cookiePair[0].trim() === 'csrftoken') {
                csrfToken = decodeURIComponent(cookiePair[1]);
                break;
            }
        }
        return csrfToken;
    }

    $('#updateAvailabilityBtn').on('click', function() {
        updateSchedule(userId);
    });

    function updateSchedule(userId) {
        var selectedDays = Array.from(document.getElementById('alwaysOffDay').selectedOptions, option => parseInt(option.value));
        console.log("Selected days for always off:", selectedDays);

        fetch(`/users/update_always_off_days/${userId}/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            },
            body: JSON.stringify({ always_off_days: selectedDays })
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                alert('Schedule updated successfully!');
                calendar.fullCalendar('refetchEvents');
            } else {
                alert('Error: ' + data.message);
            }
        })
        .catch(error => {
            console.error('Error:', error);
        });
    }
});
