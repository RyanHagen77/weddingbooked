$(document).ready(function () {
    function initializeTaskListEventListeners() {
        if (!$('#showCompletedTasks').is(':checked')) {
            $('.task-completed').hide();
        }

        $('#showCompletedTasks').off('change').change(function () {
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

        // Ensure task_type and other IDs are correctly included
        if (!formData.some(field => field.name === 'task_type')) {
            let contractId = $('#id_contract').val();
            let taskType = contractId ? 'contract' : 'internal';
            formData.push({ name: 'type', value: taskType });
        }

        // Ensure contract and note IDs are present in formData
        if (!formData.some(field => field.name === 'contract')) {
            let contractId = $('#id_contract').val() || '';
            formData.push({ name: 'contract', value: contractId });
        }

        if (!formData.some(field => field.name === 'note')) {
            let noteId = $('#id_note').val() || '';
            formData.push({ name: 'note', value: noteId });
        }

        console.log("Form Data before submission:", formData);

        $.ajax({
            type: 'POST',
            url: createTaskUrl,
            data: $.param(formData),
            success: function (response) {
                if (response.success) {
                    location.reload(); // Reload or update dynamically as needed
                } else {
                    console.error("Error:", response.errors);
                    submitButton.prop('disabled', false);
                }
            },
            error: function (xhr, status, error) {
                console.error("Error creating task:", error);
                submitButton.prop('disabled', false);
            }
        });
    });

    // Handle showing the add task modal
    $('#addTaskModal').on('show.bs.modal', function (event) {
        let button = $(event.relatedTarget);
        let senderId = button.data('sender-id');
        let contractId = button.data('contract-id') || ''; // Ensure empty string if undefined
        let noteId = button.data('note-id') || ''; // Ensure empty string if undefined
        let taskType = button.data('type') || '';// Default to 'internal'

        let modal = $(this);
        modal.find('#id_sender').val(senderId);
        modal.find('#id_contract').val(contractId);
        modal.find('#id_note').val(noteId);
        modal.find('#id_task_type').val(taskType); // Set the task type

        console.log('Modal opened. Sender ID:', senderId, 'Contract ID:', contractId, 'Note ID:', noteId, 'Task Type:', taskType);
    });

    // Handle editing a task
    $('#editTaskForm').off('submit').on('submit', function (event) {
        event.preventDefault();
        let form = $(this);
        let submitButton = form.find('button[type="submit"]');
        submitButton.prop('disabled', true);

        // Collect form data
        let formData = form.serializeArray();

        // Ensure contract and note IDs are included
        if (!formData.some(field => field.name === 'contract')) {
            let contractId = $('#id_contract').val() || '';
            formData.push({ name: 'contract', value: contractId });
        }

        if (!formData.some(field => field.name === 'note')) {
            let noteId = $('#id_note').val() || '';
            formData.push({ name: 'note', value: noteId });
        }

        // Ensure task_type is correctly included
        if (!formData.some(field => field.name === 'task_type')) {
            formData.push({ name: 'task_type', value: $('#id_task_type').val() });
        }

        console.log("Form Data before submission:", formData);

        $.ajax({
            type: 'POST',
            url: form.attr('action'),
            data: $.param(formData),
            success: function (response) {
                if (response.success) {
                    $('#taskListContainer tbody').html(response.task_list_html);
                    $('#editTaskModal').modal('hide');
                    initializeTaskListEventListeners();
                } else {
                    console.error("Error:", response.errors);
                }
                submitButton.prop('disabled', false);
            },
            error: function (xhr, status, error) {
                console.error("Error updating task:", error);
                submitButton.prop('disabled', false);
            }
        });
    });

    // Show edit task modal with data
    $(document).on('click', '.edit-task-btn', function () {
        let taskId = $(this).data('task-id');
        let senderId = $(this).data('sender-id');
        let assignedToId = $(this).data('assigned-to-id');
        let dueDate = $(this).data('due-date');
        let description = $(this).data('description');
        let taskType = $(this).data('type'); // Ensure data attribute matches correctly
        let contractId = $(this).data('contract-id');
        let noteId = $(this).data('note-id');

        // Populate form fields
        $('#editTaskForm #id_sender').val(senderId);
        $('#editTaskForm #id_assigned_to').val(assignedToId);
        $('#editTaskForm #id_due_date').val(dueDate);
        $('#editTaskForm #id_description').val(description);
        $('#editTaskForm #id_task_type').val(taskType);
        $('#editTaskForm #id_contract').val(contractId);
        $('#editTaskForm #id_note').val(noteId);

        console.log(`Modal opened with taskType: ${taskType}, Contract ID: ${contractId}, Note ID: ${noteId}`);

        // Update the form action URL
        let updateUrl = `/communication/tasks/update/${taskId}/`;
        $('#editTaskForm').attr('action', updateUrl);
    });

    // Handle marking a task as complete
    $(document).on('change', '.mark-complete-checkbox', function () {
        let taskId = $(this).closest('form').data('task-id');
        let markCompleteUrl = $(this).data('mark-complete-url');
        $.ajax({
            type: 'POST',
            url: markCompleteUrl,
            headers: {
                'X-CSRFToken': $('input[name="csrfmiddlewaretoken"]').val()
            },
            success: function (response) {
                if (response.success) {
                    $('#taskListContainer tbody').html(response.task_list_html);
                    updateTaskListAfterCompletion();
                } else {
                    alert("Task could not be marked as complete.");
                }
            },
            error: function (xhr, status, error) {
                console.error("Error marking task as complete:", error);
            }
        });
    });

    // Initialize task list event listeners on page load
    initializeTaskListEventListeners();
});
