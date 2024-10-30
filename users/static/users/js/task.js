$(document).ready(function () {
    // Initialize task list event listeners
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

    // Update task list container with AJAX response
    function updateTaskListContainer(response) {
        if (response.success) {
            $('#taskListContainer tbody').html(response.task_list_html);
            initializeTaskListEventListeners(); // Re-initialize JavaScript
        } else {
            console.error("Error:", response.errors);
        }
    }

    // Handle adding a new task
    $('#addTaskForm').off('submit').on('submit', function (event) {
        event.preventDefault();
        let createTaskUrl = $(this).data('create-task-url');
        let formData = $(this).serializeArray();
        let submitButton = $(this).find('button[type="submit"]');

        submitButton.prop('disabled', true);
        formData = formData.filter(field => field.name !== 'task_type' || field.value !== '');
        formData.push({ name: 'task_type', value: 'contract' }); // Default task_type value

        $.ajax({
            type: 'POST',
            url: createTaskUrl,
            data: $.param(formData),
            success: function(response) {
                if (response.success) {
                    location.reload();
                } else {
                    console.error("Error:", response.errors);
                    submitButton.prop('disabled', false);
                }
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
        let taskType = button.data('task-type') || 'internal'; // Default task_type value
        let modal = $(this);

        modal.find('#id_sender').val(senderId);
        modal.find('#id_contract').val(contractId);
        modal.find('#id_note').val(noteId);
        modal.find('#id_task_type').val(taskType); // Set the task type

        console.log('Modal opened. Sender ID:', senderId, 'Contract ID:', contractId, 'Note ID:', noteId, 'Task Type:', taskType);
    });

    // Handle editing a task
    $('#editTaskForm').off('submit').on('submit', function(event) {
        event.preventDefault();
        let form = $(this);
        let submitButton = form.find('button[type="submit"]');

        submitButton.prop('disabled', true);
        let formData = form.serializeArray();

        formData = formData.filter(field => field.name !== 'task_type' || field.value !== '');
        formData.push({ name: 'task_type', value: 'internal' }); // Default task_type value

        $.ajax({
            type: 'POST',
            url: form.attr('action'),
            data: $.param(formData),
            success: function(response) {
                if (response.success) {
                    $('#taskListContainer tbody').html(response.task_list_html);
                    $('#editTaskModal').modal('hide');
                    initializeTaskListEventListeners();
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
        let taskType = $(this).data('task-type') || 'internal'; // Default task_type value

        $('#editTaskForm #id_sender').val(senderId);
        $('#editTaskForm #id_assigned_to').val(assignedToId);
        $('#editTaskForm #id_due_date').val(dueDate);
        $('#editTaskForm #id_description').val(description);
        $('#editTaskForm #id_task_type').val(taskType);

        let updateUrl = `/communication/tasks/update/${taskId}/`; // Update URL to reflect the communication app
        $('#editTaskForm').attr('action', updateUrl);
    });

    // Handle marking a task as complete
    $(document).on('submit', '.mark-complete-form', function(event) {
        event.preventDefault();
        let form = $(this);

        $.ajax({
            type: 'POST',
            url: form.attr('action'),
            data: form.serialize(),
            success: function(response) {
                updateTaskListContainer(response);
            },
            error: function(xhr, status, error) {
                console.error("Error marking task as complete:", error);
            }
        });
    });

    // Initialize task list event listeners on page load
    initializeTaskListEventListeners();
});