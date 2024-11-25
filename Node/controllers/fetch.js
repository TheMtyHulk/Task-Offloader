
document.addEventListener('DOMContentLoaded', function() {
    fetch('/files')
        .then(response => response.json())
        .then(files => {
            loadFiles(files);
        })
        .catch(error => {
            console.error('Error fetching files:', error);
            const filesList = document.getElementById('files-list');
            const errorMessage = document.createElement('p');
            errorMessage.textContent = 'Error fetching files';
            filesList.appendChild(errorMessage);
        });
});

// to handle the uploading of files
async function handleUploadAndSchedule(event) {
    event.preventDefault();

    // Trigger the schedule tasks logic
  //   await scheduleTasks();

    // Proceed with the file upload
    const form = event.target;
    const formData = new FormData(form);

  // Add the selected radio button value to the FormData
  const conversionType = document.querySelector('input[name="conversionType"]:checked');
    if (conversionType) {
      formData.append('conversionType', conversionType.value);
    }

    try {
      const response = await fetch(form.action, {
        method: form.method,
        body: formData
      });

      const result = await response.json();
      document.getElementById('message').innerText = result.message || result.err;
    } catch (err) {
      document.getElementById('message').innerText = 'Error uploading files';
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