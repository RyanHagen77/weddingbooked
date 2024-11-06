$(document).ready(function() {
    // Retrieve the CSRF token from the document and check if it's valid
    let csrftoken = $('#csrf-token').val();
    if (csrftoken) {
        $.ajaxSetup({
            headers: { "X-CSRFToken": csrftoken }
        });
    } else {
        console.warn("CSRF token not found on the page.");
    }

    // Retrieve the add note URL and ensure it exists
    let addNoteURL = $('body').data('add-note-url');
    if (!addNoteURL) {
        console.warn("addNoteURL is not set. Check if data-add-note-url attribute is present on <body>.");
    }

    // Check if the form exists before attaching the submit event listener
    let addNoteForm = $('#addNoteForm');
    if (addNoteForm.length) {
        addNoteForm.on('submit', function(event) {
            event.preventDefault(); // Prevents the form from submitting normally

            let formData = $(this).serialize(); // Serialize the form data

            $.ajax({
                type: 'POST',
                url: addNoteURL, // Uses the URL directly
                data: formData,
                success: function(response) {
                    if (response.success) {
                        // Append the new note to the contract notes list
                        if (response.contract_id) {
                            let notesList = $('#notes-list-' + response.contract_id);
                            if (notesList.length) {
                                notesList.append(`
                                    <div class="message mt-2 p-2 border border-gray-300 rounded">
                                        <p>${response.content}</p>
                                    </div>
                                `);
                            } else {
                                console.warn("Notes list container not found for contract ID:", response.contract_id);
                            }
                        }

                        // Clear the form fields and close the modal
                        $('#addNoteForm textarea[name="content"]').val('');
                        $('#addNoteModal').modal('hide');
                    } else {
                        alert("Error adding note: " + response.error);
                    }
                },
                error: function(xhr, status, error) {
                    console.error("An error occurred:", error);
                }
            });
        });
    } else {
        console.warn("addNoteForm is not found on the page.");
    }

    // Modal showing event for setting form fields
    $('#addNoteModal').on('show.bs.modal', function(event) {
        let button = $(event.relatedTarget); // Button that triggered the modal
        let contractId = button.data('contract-id'); // Retrieve contract ID from button data attribute
        let noteType = button.data('note-type'); // Retrieve note type from button data attribute

        if (!contractId) {
            console.warn("contractId is missing from the modal trigger button.");
        }
        if (!noteType) {
            console.warn("noteType is missing from the modal trigger button.");
        }

        let modal = $(this);

        // Set the contract ID and note type in the form's hidden fields
        modal.find('input[name="contract_id"]').val(contractId || ''); // Default to empty string if missing
        modal.find('input[name="note_type"]').val(noteType || '');

        console.log('Modal opened for contract ID:', contractId, 'Note Type:', noteType); // Debugging
    });
});
