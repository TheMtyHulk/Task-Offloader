
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
        scheduleTasks();
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
        
             if (file.contentType) {
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
                    //    iframeButton.style.display = 'inline-block'; // Hide the view in iframe button
                    checkComputedAt();
            };
cardBody.appendChild(hideDetailsButton);
const checkComputedAt = async () => {
    while (true) {
        try {
            const response = await fetch(`/filedetails/${file._id}`);
            const result = await response.json();
            if (result.completed_at) {
                downloadButton.style.display = 'inline-block';
                iframeButton.style.display = 'inline-block';
                break; // Exit the loop once the condition is met
            } else {
                downloadButton.style.display = 'none';
                iframeButton.style.display = 'none';
            }
        } catch (err) {
            console.error('Error fetching file details', err);
            
        }
        await new Promise(resolve => setTimeout(resolve, 1000)); // Wait for 1 second before checking again
    }
};
checkComputedAt();
            viewDetailsButton.onclick = async function() {
                try {
                    const response = await fetch(`/filedetails/${file._id}`);
                    const result = await response.json();
                    detailsDiv.innerHTML = `
                        <div class="card mb-3">
                            <p>Task ID: ${result._id || 'N/A'}</p>
                            <p>Command: ${result.command || 'N/A'}</p>
                            <p>Scheduled At: ${result.scheduled_at ? new Date(result.scheduled_at).toLocaleString() : 'N/A'}</p>
                            <p>Picked At: ${result.picked_at ? result.picked_at : 'N/A'}</p>
                            <p>Started At: ${result.started_at ? new Date(result.started_at).toLocaleString() : 'N/A'}</p>
                            <p>Completed At: ${result.completed_at ? new Date(result.completed_at).toLocaleString() : 'N/A'}</p>
                            <!--<p>Completed By: ${result.completed_by || 'N/A'}</p>-->
                            <p>Computed At: ${result.assigned_to ? result.assigned_to: 'N/A'}</p>
                            <p>Operation: ${result.operation || 'N/A'}</p>
                        </div>`;
                    detailsDiv.style.display = 'block'; // Show the details
                    //
                    hideDetailsButton.style.display = 'inline-block'; // Show the hide button
                viewDetailsButton.style.display = 'none'; // Hide the view button
                
                //
                // Show download button only if assigned_to is not "N/A"
                // if (result.completed_at) {
                //     downloadButton.style.display = 'inline-block';
                //     iframeButton.style.display = 'inline-block'
                // } else {
                //     downloadButton.style.display = 'none';
                //     iframeButton.style.display = 'none';
                // }
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

            //download button
            
            const downloadButton = document.createElement('button');
            downloadButton.type = 'button';
            downloadButton.className = 'btn btn-primary';
            downloadButton.textContent = 'Download';
            downloadButton.style.display = 'none'; // Initially
            downloadButton.onclick = function() {
                const link = document.createElement('a');
                link.href = `files/${file.filename}`;
                link.download = file.filename.includes('.') ? file.filename : `${file.filename}.${file.contentType.split('/')[1]}`;
                link.click();
            };
            form.appendChild(downloadButton);
            form.appendChild(button);

            const iframeButton = document.createElement('button');
            iframeButton.type = 'button';
            iframeButton.className = 'btn btn-secondary';
            iframeButton.textContent = 'View in Iframe';
            iframeButton.style.display = 'none';
            iframeButton.style.float = 'right';
            iframeButton.onclick = function() {
                if (file.contentType.startsWith('video/')) {
                    const video = document.createElement('video');
                    const source = document.createElement('source');
                    source.src = `files/${file.filename}`;
                    source.type = file.contentType;
                    video.style.width = '100%';
                    video.style.height = 'auto';
                    video.controls = true;
                    video.appendChild(source);
                    detailsDiv.innerHTML = ''; // Clear previous content
                    detailsDiv.appendChild(video);
                    detailsDiv.style.display = 'block'; // Show the video
                    hideDetailsButton.style.display = 'inline-block'; // Show the hide button
                    viewDetailsButton.style.display = 'none'; // Hide the view button
                    iframeButton.style.display = 'none'; // Hide the view in iframe button
                } else if (file.contentType.startsWith('image/')) {
                    const imge = document.createElement('img');
                    imge.src = `files/${file.filename}`;
                    imge.style.width = '100%';
                    imge.alt = '';
                    imge.className = 'img-responsive';
                    detailsDiv.innerHTML = ''; // Clear previous content
                    const popupButton = document.createElement('button');
                    popupButton.textContent = 'Popup';
                    popupButton.style.marginTop = '10px';
                    popupButton.onclick = function() {
                        document.body.appendChild(popup);
                    };
                    detailsDiv.appendChild(popupButton);
//
                    const popup = document.createElement('div');
                    popup.style.position = 'fixed';
                    popup.style.top = '50%';
                    popup.style.left = '50%';
                    popup.style.width = '60%';
                    popup.style.height = '60%';
                    popup.style.overflow = 'auto';
                    popup.style.transform = 'translate(-50%, -50%)';
                    popup.style.backgroundColor = 'white';
                    popup.style.padding = '20px';
                    popup.style.boxShadow = '0 0 10px rgba(0, 0, 0, 0.5)';
                    popup.style.zIndex = '1000';

                    const img = document.createElement('img');
                    img.src = `files/${file.filename}`;
                    img.style.width = '100%';
                    img.alt = '';
                    img.className = 'img-responsive';


                    const zoomInButton = document.createElement('button');
                    zoomInButton.className = 'btn btn-primary';
                    zoomInButton.textContent = 'Zoom In';
                    zoomInButton.style.marginTop = '10px';
                    zoomInButton.onclick = function() {
                        img.style.width = (img.clientWidth * 1.2) + 'px';
                    };
                    popup.appendChild(zoomInButton);

                    const zoomOutButton = document.createElement('button');
                    zoomOutButton.className = 'btn btn-secondary';
                    zoomOutButton.textContent = 'Zoom Out';
                    zoomOutButton.style.marginTop = '10px';
                    zoomOutButton.onclick = function() {
                        img.style.width = (img.clientWidth / 1.2) + 'px';
                    };
                    popup.appendChild(zoomOutButton);

                    const closeButton = document.createElement('button');
                    closeButton.className = 'btn btn-danger';
                    closeButton.textContent = 'Close';
                    closeButton.style.marginTop = '10px';
                    closeButton.onclick = function() {
                        document.body.removeChild(popup);
                    };
                    popup.appendChild(closeButton);
                    popup.appendChild(img);
                    // detailsDiv.appendChild(popup);

                    detailsDiv.appendChild(imge);
                    detailsDiv.style.display = 'block'; // Show the image
                    hideDetailsButton.style.display = 'inline-block'; // Show the hide button
                    viewDetailsButton.style.display = 'none'; // Hide the view button
                    iframeButton.style.display = 'none'; // Hide the view in iframe button
                }
                else {
                const iframe = document.createElement('iframe');
                
                iframe.src = `files/${file.filename}`;
                iframe.width = '100%';
                iframe.height = '500px';
                iframe.style.border = 'none';
                detailsDiv.innerHTML = ''; // Clear previous content
                detailsDiv.appendChild(iframe);
                detailsDiv.style.display = 'block'; // Show the iframe
                hideDetailsButton.style.display = 'inline-block'; // Show the hide button
                viewDetailsButton.style.display = 'none'; // Hide the view button
                iframeButton.style.display = 'none'; // Hide the view in iframe button
                }
            };
            cardBody.appendChild(iframeButton);            
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


  // Schedule tasks
  async function scheduleTasks() {
    try {
      const response = await fetch('/schedule-tasks', {
        method: 'POST'
      });

      const result = await response.json();
      document.getElementById('message').innerText = result.message || result.err;
    } catch (err) {
      document.getElementById('message').innerText = 'Error scheduling tasks';
    }
  }