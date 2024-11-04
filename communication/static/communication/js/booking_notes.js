$(document).ready(function() {
    let csrftoken = $('#csrf-token').val(); // Retrieve the token from the document

    $.ajaxSetup({
        headers: { "X-CSRFToken": csrftoken }
    });

    let addNoteURL = $('body').data('add-note-url'); // Retrieve the URL

    // Form submission for adding a note
    $('#addNoteForm').on('submit', function(event) {
        event.preventDefault(); // Prevents the form from submitting normally

        let formData = $(this).serialize(); // Serialize the form data
        $.ajax({
            type: 'POST',
            url: addNoteURL, // Uses the URL directly
            data: formData,
            success: function(response) {
                if (response.success) {
                    // Append the new note to the contract notes list
                    $('#notes-list-' + response.contract_id).append(`
                        <div class="message">
                            <p>${response.content}</p>
                        </div>
                    `); // Update contract notes

                    // Clear the form fields and close the modal
                    $('#addNoteForm textarea[name="content"}').val('');
                    $('#addNoteModal').modal('hide');
                } else {
                    alert("Error adding note: " + response.error);
                }
            },
            error: function(xhr, status, error) {
                console.error("An error occurred: " + error);
            }
        });
    });

    // Modal showing for setting fields
    $('#addNoteModal').on('show.bs.modal', function(event) {
        let button = $(event.relatedTarget); // Button that triggered the modal
        let contractId = button.data('contract-id'); // Retrieve contract ID from button data attribute
        let noteType = button.data('note-type'); // Retrieve note type from button data attribute

        let modal = $(this);

        // Set the contract ID and note type in the form's hidden fields
        modal.find('input[name="contract_id"]').val(contractId);
        modal.find('input[name="note_type"]').val(noteType);

        console.log('Modal opened for contract ID:', contractId, 'Note Type:', noteType); // Debugging
    });
});
