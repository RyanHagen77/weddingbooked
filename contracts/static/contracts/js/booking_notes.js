$(document).ready(function() {
    // CSRF token setup for AJAX requests
    let csrftoken = $('#csrf-token').val();

    $.ajaxSetup({
        headers: { "X-CSRFToken": csrftoken }
    });

    // Add a note
    $(document).ready(function() {
    $('.add-note-btn').click(function() {
    let bookingId = $(this).data('booking-id');
    let noteContent = $('#new-note-content-' + bookingId).val();
    let addNoteURL = $('body').data('add-note-url');

    if (noteContent) {
        $.ajax({
            url: addNoteURL,
            method: 'POST',
            data: {
                content: noteContent,
                booking_id: bookingId,
                csrfmiddlewaretoken: csrftoken
            },
            success: function(response) {
                if (response.success) {
                    let newNoteHtml = `
                        <li id="note-${response.note_id}">
                            <p>${noteContent}</p>
                            <p>Author: ${response.author}</p>
                            <p>Timestamp: ${response.timestamp}</p>
                            <button class="edit-note" data-note-id="${response.note_id}">Edit</button>
                            <button class="delete-note" data-note-id="${response.note_id}">Delete</button>
                        </li>
                    `;

                    let bookingNotesList = $('#notes-list-' + bookingId);
                    bookingNotesList.append(newNoteHtml);

                    // Clear the textarea content after successfully adding the note
                    $('#new-note-content-' + bookingId).val('');
                } else {
                    alert("Error adding note.");
                }
            },
            error: function(xhr, status, error) {
                let errorMessage = 'An error occurred.';
                if (xhr.responseJSON && xhr.responseJSON.error) {
                    errorMessage = xhr.responseJSON.error;
                }
                alert(errorMessage);
            }
        });
    }
});
});

    // Edit a note
    $(document).on('click', '.edit-note', function() {
    let noteId = $(this).data('note-id');
    let noteContent = $(`#note-${noteId} p`).first().text();  // Get only the first <p> element's text

    // Show the note content in the prompt
    let newContent = prompt("Edit note:", noteContent);

    if (newContent !== null) {  // Check if user didn't cancel
        let editNoteURL = $(this).data('url-base').replace('0', noteId);  // Using Django URL template tag with dynamic replacement

        $.ajax({
            url: editNoteURL,
            method: 'POST',
            data: {
                content: newContent,
                csrfmiddlewaretoken: csrftoken
            },
            success: function(response) {
                if (response.success) {
                    // Update the note content
                    $(`#note-${noteId} p`).first().text(newContent);
                } else {
                    alert("Error editing note.");
                }
            }
        });
    }
});



    $(document).on('click', '.save-note', function() {
    let noteId = $(this).data('note-id');
    let noteElement = $(this).closest('li');

    // Get the edited content from the textarea
    let newContent = noteElement.find('.note-edit-content').val();

    let editNoteURL = $(this).data('url-base');

    if (newContent) {
        $.ajax({
            url: editNoteURL,
            method: 'POST',
            data: {
                content: newContent,
                csrfmiddlewaretoken: csrftoken
            },
            success: function(response) {
                if (response.success) {
                    // Update the note content and toggle back to display mode
                    noteElement.find('.note-content').text(newContent).show();
                    noteElement.find('.note-edit-content').hide();
                    noteElement.find('.edit-note').show();
                    noteElement.find('.delete-note').show();
                    noteElement.find('.save-note').hide();
                    noteElement.find('.cancel-edit').hide();
                } else {
                    alert("Error editing note.");
                }
            }
        });
    }
});



    $(document).on('click', '.cancel-edit', function() {
        let noteId = $(this).data('note-id');
        let noteElement = $(this).closest('li');

        // Toggle back to display mode without saving changes
        noteElement.find('.note-content').show();
        noteElement.find('.note-edit-content').hide();
        noteElement.find('.edit-note').show();
        noteElement.find('.delete-note').show();
        noteElement.find('.save-note').hide();
        noteElement.find('.cancel-edit').hide();
    });


    // Delete a note
    $(document).on('click', '.delete-note', function() {
    let noteId = $(this).data('note-id');
    let deleteNoteURL = $(this).data('url-base').replace('0', noteId);

    if (confirm("Are you sure you want to delete this note?")) {
        $.ajax({
            url: deleteNoteURL,
            method: 'POST',
            data: {
                csrfmiddlewaretoken: csrftoken
            },
            success: function(response) {
                if (response.success) {
                    $(`#note-${noteId}`).remove();
                } else {
                    alert("Error deleting note.");
                }
            }
        });
    }
});
});





