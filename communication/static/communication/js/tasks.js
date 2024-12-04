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
    $('#addTaskModal').off('show.bs.modal').on('show.bs.modal', function (event) {
            let button = $(event.relatedTarget); // Button that triggered the modal
            let senderId = button.data('sender-id');
            let contractId = button.data('contract-id') || ''; // Default to empty string
            let noteId = button.data('note-id') || ''; // Default to empty string
            let taskType = button.data('type') || 'internal'; // Default to 'internal'

            let modal = $(this);

            // Reset form fields and populate them
            modal.find('#addTaskForm')[0].reset();
            modal.find('#id_sender').val(senderId);
            modal.find('#id_contract').val(contractId);
            modal.find('#id_note').val(noteId);
            modal.find('#id_task_type').val(taskType);

            console.log('Opening Add Task Modal with Data:', { senderId, contractId, noteId, taskType });
        });

        // Handle task creation form submission
        $('#addTaskForm').off('submit').on('submit', function (event) {
            event.preventDefault();
            let form = $(this);
            let createTaskUrl = form.data('create-task-url');
            let submitButton = form.find('button[type="submit"]');
            submitButton.prop('disabled', true);

            let formData = form.serializeArray();

            // Remove duplicate `sender` or other conflicting fields
            formData = formData.filter((field, index, self) =>
                index === self.findIndex(f => f.name === field.name)
            );

            // Ensure required fields are correctly populated
            let contractId = $('#id_contract').val() || '';
            let noteId = $('#id_note').val() || '';
            let taskType = contractId ? 'contract' : 'internal';

            // Add or update necessary fields
            formData = formData.filter(field => !['task_type', 'contract', 'note'].includes(field.name));
            formData.push({ name: 'task_type', value: taskType });
            formData.push({ name: 'contract', value: contractId });
            formData.push({ name: 'note', value: noteId });

            console.log("Submitting Task Form Data:", formData);

            $.ajax({
                type: 'POST',
                url: createTaskUrl,
                data: $.param(formData),
                success: function (response) {
                    if (response.success) {
                        location.reload(); // Reload to update task list
                    } else {
                        console.error("Error:", response.errors);
                        alert("Error saving task. Please check the form.");
                    }
                    submitButton.prop('disabled', false);
                },
                error: function (xhr, status, error) {
                    console.error("Error saving task:", error);
                    alert("An error occurred while saving the task. Please try again.");
                    submitButton.prop('disabled', false);
                }
            });
        });


 // Show Edit Task Modal with Pre-filled Data
    $(document).on('click', '.edit-task-btn', function () {
        let taskId = $(this).data('task-id');
        let senderId = $(this).data('sender-id');
        let assignedToId = $(this).data('assigned-to-id');
        let dueDate = $(this).data('due-date');
        let description = $(this).data('description');
        let taskType = $(this).data('type');
        let contractId = $(this).data('contract-id');
        let noteId = $(this).data('note-id');

        // Populate form fields
        let modal = $('#editTaskModal');
        modal.find('#id_task').val(taskId);
        modal.find('#id_sender').val(senderId);
        modal.find('#id_assigned_to').val(assignedToId);
        modal.find('#id_due_date').val(dueDate);
        modal.find('#id_description').val(description);
        modal.find('#id_task_type').val(taskType);
        modal.find('#id_contract').val(contractId);
        modal.find('#id_note').val(noteId);

        console.log(`Editing Task: ID=${taskId}, Type=${taskType}, Contract=${contractId}, Note=${noteId}`);

        // Update form's URL for editing
        let updateUrl = `/communication/tasks/update/${taskId}/`;
        modal.find('#editTaskForm').attr('data-update-task-url', updateUrl);
        modal.modal('show');
    });

    // Handle Task Update Submission
    $('#editTaskForm').off('submit').on('submit', function (event) {
        event.preventDefault();
        let form = $(this);
        let updateTaskUrl = form.attr('data-update-task-url');
        let submitButton = form.find('button[type="submit"]');
        submitButton.prop('disabled', true);

        let formData = form.serializeArray();

        console.log("Submitting Edit Task Form Data:", formData);

        $.ajax({
            type: 'POST',
            url: updateTaskUrl,
            data: $.param(formData),
            success: function (response) {
                if (response.success) {
                    location.reload(); // Reload to update task list
                } else {
                    console.error("Error:", response.errors);
                    alert("Error saving task. Please check the form.");
                }
                submitButton.prop('disabled', false);
            },
            error: function (xhr, status, error) {
                console.error("Error saving task:", error);
                alert("An error occurred while saving the task. Please try again.");
                submitButton.prop('disabled', false);
            }
        });
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


    initializeTaskListEventListeners();
});
