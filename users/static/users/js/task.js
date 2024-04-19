$('#addTaskForm').on('submit', function (event) {
    event.preventDefault();
    let createTaskUrl = $(this).data('create-task-url');  // Get the URL from the data attribute
    let formData = $(this).serialize();
    $.ajax({
        type: 'POST',
        url: createTaskUrl,
        data: formData,
        success: function(response) {
            if (response.success) {
                // Close the modal
                $('#addTaskModal').modal('hide');
                // Update the task list with the HTML returned by the server
                $('#taskListContainer').html(response.task_list_html);
            } else {
                // Handle errors
            }
        },
        error: function(xhr, status, error) {
            // Handle error
        }
    });
});

$('#addTaskModal').on('show.bs.modal', function (event) {
    let button = $(event.relatedTarget); // Button that triggered the modal
    let senderId = button.data('sender-id');
    let contractId = button.data('contract-id');
    let noteId = button.data('note-id');
    let modal = $(this);

    // Set the values in the form's hidden fields
    modal.find('#id_sender').val(senderId);
    modal.find('#id_contract').val(contractId);
    modal.find('#id_note').val(noteId);

    // Print the values for debugging
    console.log('Modal opened. Sender ID:', senderId, 'Contract ID:', contractId, 'Note ID:', noteId);
});


// Handle form submission for updating a task
$('#editTaskForm').on('submit', function(event) {
    event.preventDefault();
    let form = $(this);
    $.ajax({
        type: 'POST',
        url: form.attr('action'),
        data: form.serialize(),
        success: function(response) {
            if (response.success) {
                // Update the task list with the HTML returned by the server
                $('#taskListContainer').html(response.task_list_html);
                // Close the modal
                $('#editTaskModal').modal('hide');
            } else {
                // Handle form errors
                // You might want to display error messages on the form
            }
        },
        error: function(xhr, status, error) {
            console.error("Error updating task:", error);
        }
    });
});

$(document).on('click', '.edit-task-btn', function(event) {
    let taskId = $(this).data('task-id');
    let senderId = $(this).data('sender-id');
    let assignedToId = $(this).data('assigned-to-id');
    let dueDate = $(this).data('due-date');
    let description = $(this).data('description');

    // Set the values in the form fields
    $('#editTaskForm #id_sender').val(senderId);
    $('#editTaskForm #id_assigned_to').val(assignedToId);
    $('#editTaskForm #id_due_date').val(dueDate);
    $('#editTaskForm #id_description').val(description);

    // Update the form action to include the task ID for the update endpoint
    let updateUrl = `/users/tasks/update/${taskId}/`;
    $('#editTaskForm').attr('action', updateUrl);
});


$(document).on('submit', '.mark-complete-form', function(event) {
    event.preventDefault();
    let form = $(this);
    $.ajax({
        type: 'POST',
        url: form.attr('action'),
        data: form.serialize(),
        success: function(response) {
            if (response.success) {
                // Update the task list with the HTML returned by the server
                $('#taskListContainer').html(response.task_list_html);
            } else {
                // Handle errors
            }
        },
        error: function(xhr, status, error) {
            // Handle error
        }
    });
});

