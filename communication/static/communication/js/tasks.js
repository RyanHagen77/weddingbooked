$(document).ready(function () {
    function initializeTaskListEventListeners() {
        if (!$('#showCompletedTasks').is(':checked')) {
            $('.task-completed').hide();
        }

        $('#showCompletedTasks').off('change').change(function() {
            if (this.checked) {
                $('.task-completed').show();
            } else {
                $('.task-completed').hide();
            }
        });
    }

    function updateTaskListAfterCompletion() {
        initializeTaskListEventListeners();
    }

    // Handle adding a new task
    $('#addTaskForm').off('submit').on('submit', function (event) {
        event.preventDefault();
        let createTaskUrl = $(this).data('create-task-url');
        let formData = $(this).serializeArray();
        let submitButton = $(this).find('button[type="submit"]');
        submitButton.prop('disabled', true);

        formData = formData.filter(field => field.name !== 'type' || field.value !== '');
        formData.push({ name: 'type', value: 'internal' }); // Default type value

        $.ajax({
            type: 'POST',
            url: createTaskUrl,
            data: $.param(formData),
            success: function(response) {
                if (response.success) {
                    $('#addTaskModal').modal('hide');
                    $('#taskListContainer tbody').html(response.task_list_html);
                    initializeTaskListEventListeners(); // Re-initialize JavaScript
                } else {
                    console.error("Error:", response.errors);
                }
                submitButton.prop('disabled', false);
            },
            error: function(xhr, status, error) {
                console.error("Error creating task:", error);
                submitButton.prop('disabled', false);
            }
        });
    });

    // Handle showing the add task modal
    $('#addTaskModal').on('show.bs.modal', function (event) {
        let button = $(event.relatedTarget);
        let senderId = button.data('sender-id');
        let contractId = button.data('contract-id');
        let noteId = button.data('note-id');
        let type = button.data('type') || 'internal'; // Default type value
        let modal = $(this);
        modal.find('#id_sender').val(senderId);
        modal.find('#id_contract').val(contractId);
        modal.find('#id_note').val(noteId);
        modal.find('#id_type').val(type); // Set the task type

        console.log('Modal opened. Sender ID:', senderId, 'Contract ID:', contractId, 'Note ID:', noteId, 'Type:', type);
    });

    // Handle editing a task
    $('#editTaskForm').off('submit').on('submit', function(event) {
        event.preventDefault();
        let form = $(this);
        let submitButton = form.find('button[type="submit"]');
        submitButton.prop('disabled', true);

        let formData = form.serializeArray();
        formData = formData.filter(field => field.name !== 'type' || field.value !== '');
        formData.push({ name: 'type', value: 'internal' }); // Default type value

        $.ajax({
            type: 'POST',
            url: form.attr('action'),
            data: $.param(formData),
            success: function(response) {
                if (response.success) {
                    $('#taskListContainer tbody').html(response.task_list_html);
                    $('#editTaskModal').modal('hide');
                    initializeTaskListEventListeners(); // Re-initialize JavaScript
                } else {
                    console.error("Error:", response.errors);
                }
                submitButton.prop('disabled', false);
            },
            error: function(xhr, status, error) {
                console.error("Error updating task:", error);
                submitButton.prop('disabled', false);
            }
        });
    });

    // Show edit task modal with data
    $(document).on('click', '.edit-task-btn', function(event) {
        let taskId = $(this).data('task-id');
        let senderId = $(this).data('sender-id');
        let assignedToId = $(this).data('assigned-to-id');
        let dueDate = $(this).data('due-date');
        let description = $(this).data('description');
        let type = $(this).data('type') || 'internal'; // Default type value
        $('#editTaskForm #id_sender').val(senderId);
        $('#editTaskForm #id_assigned_to').val(assignedToId);
        $('#editTaskForm #id_due_date').val(dueDate);
        $('#editTaskForm #id_description').val(description);
        $('#editTaskForm #id_type').val(type); // Set the task type

        let updateUrl = `/users/tasks/update/${taskId}/`;
        $('#editTaskForm').attr('action', updateUrl);
    });

    // Handle marking a task as complete
    $(document).on('change', '.mark-complete-checkbox', function() {
        let taskId = $(this).closest('form').data('task-id');
        let markCompleteUrl = $(this).data('mark-complete-url');
        $.ajax({
            type: 'POST',
            url: markCompleteUrl,
            headers: {
                'X-CSRFToken': $('input[name="csrfmiddlewaretoken"]').val()
            },
            success: function(response) {
                if (response.success) {
                    $('#taskListContainer tbody').html(response.task_list_html);
                    updateTaskListAfterCompletion();
                } else {
                    alert("Task could not be marked as complete.");
                }
            },
            error: function(xhr, status, error) {
                console.error("Error marking task as complete:", error);
            }
        });
    });

    // Initialize task list event listeners on page load
    initializeTaskListEventListeners();
});
