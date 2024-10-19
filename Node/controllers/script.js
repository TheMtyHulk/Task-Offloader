
//function to read files
function readMultipleFiles(files) {
    const fileNames = Array.from(files).map(file => file.name).join(', ');
    document.getElementById("file-label").textContent = fileNames;
}


//function to load files
function loadFiles(files) {
    const filesList = document.getElementById('files-list');
    filesList.innerHTML = ''; // Clear existing content

    if (files && files.length > 0) {
        files.forEach(function(file) {
            const card = document.createElement('div');
            card.className = 'card mb-3';

            //card header
            const cardHeader = document.createElement('div');
            cardHeader.className = 'card-header';
            const cardTitle = document.createElement('div');
            cardTitle.className = 'card-title';
            cardTitle.textContent = file.filename;
            cardHeader.appendChild(cardTitle);

            //card body
            const cardBody = document.createElement('div');
            cardBody.className = 'card-body';
            if (file.isImage) {
                const img = document.createElement('img');
                img.src = `image/${file.filename}`;
                img.width = 250;
                img.alt = '';
                img.className = 'img-responsive';
                cardBody.appendChild(img);
            } else {
                const link = document.createElement('a');
                link.href = `files/${file.filename}`;
                link.download = file.filename;
                link.textContent = file.filename;
                cardBody.appendChild(link);
            }

            // button to show the file details
            const viewDetailsButton = document.createElement('button');
            viewDetailsButton.className = 'btn btn-info';
            viewDetailsButton.style.float = 'left';
            viewDetailsButton.textContent = 'View Details';

            
            // to show the file details
            const detailsDiv = document.createElement('div');
            detailsDiv.id = `details-${file._id}`;
            detailsDiv.style.display = 'none'; // Initially hidden
            cardBody.appendChild(detailsDiv);

   // button to hide the file details
   const hideDetailsButton = document.createElement('button');
   hideDetailsButton.className = 'btn btn-secondary';
   hideDetailsButton.textContent = 'Hide Details';
   hideDetailsButton.style.display = 'none'; // Hide the hide button
   hideDetailsButton.onclick = function() {
       detailsDiv.style.display = 'none'; // Hide the details
       hideDetailsButton.style.display = 'none'; // Hide the hide button
           viewDetailsButton.style.display = 'inline-block'; // Show the view button
   };
   cardBody.appendChild(hideDetailsButton);

            viewDetailsButton.onclick = async function() {
                try {
                    const response = await fetch(`/filedetails/${file._id}`);
                    const result = await response.json();
                    detailsDiv.innerHTML = `
                        <div class="card mb-3">
                            <p>Task ID: ${result._id || 'N/A'}</p>
                            <p>Command: ${result.command || 'N/A'}</p>
                            <p>Scheduled At: ${result.scheduled_at ? new Date(result.scheduled_at).toLocaleString() : 'N/A'}</p>
                            <p>Picked At: ${result.picked_at ? new Date(result.picked_at).toLocaleString() : 'N/A'}</p>
                            <p>Started At: ${result.started_at ? new Date(result.started_at).toLocaleString() : 'N/A'}</p>
                            <p>Completed At: ${result.completed_at ? new Date(result.completed_at).toLocaleString() : 'N/A'}</p>
                            <p>Completed By: ${result.completed_by || 'N/A'}</p>
                            <p>Computed At: ${result.computed_at ? new Date(result.computed_at).toLocaleString() : 'N/A'}</p>
                            <p>Operation: ${result.operation || 'N/A'}</p>
                        </div>`;
                    detailsDiv.style.display = 'block'; // Show the details
                    //
                    hideDetailsButton.style.display = 'inline-block'; // Show the hide button
                viewDetailsButton.style.display = 'none'; // Hide the view button
                //
                } catch (err) {
                    detailsDiv.innerText = 'Error fetching file details';
                    detailsDiv.style.display = 'block'; // Show the error message
                }
            };           
             
            //card footer
            const cardFooter = document.createElement('div');
            cardFooter.className = 'card-footer';
            const form = document.createElement('form');
            form.action = `/files/del/${file._id}`;
            form.method = 'post';
            const button = document.createElement('button');
            button.type = 'submit';
            button.className = 'btn btn-danger';
            button.textContent = 'Remove';
            form.appendChild(button);
            cardFooter.appendChild(viewDetailsButton);
            cardFooter.appendChild(form);
            
            
            card.appendChild(cardHeader);
            card.appendChild(cardBody);
            card.appendChild(cardFooter);

            filesList.appendChild(card);
        });
    } else {
        const noFilesMessage = document.createElement('p');
        noFilesMessage.textContent = 'No files to show';
        filesList.appendChild(noFilesMessage);
    }
}
