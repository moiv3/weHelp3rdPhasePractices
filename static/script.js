
function addUploadButtonListener(){
    document.getElementById('upload-form').addEventListener('submit', async function(event){
        event.preventDefault();

        const messageInput = document.querySelector('#text-id').value;
        console.log(messageInput);

        if (!messageInput){
            document.querySelector('#upload-status-message').textContent = 'You suck. Please enter a message.';
            return;
        }

        const fileInput = document.querySelector('#file-id');
        // console.log(fileInput);
        console.log(fileInput.files[0]);
        const file = fileInput.files[0];

        if (!file){
            document.querySelector('#upload-status-message').textContent = 'You suck. Pick a file please.';
            return;
        }

        const fileSizeMb = (file.size / 1024 / 1024).toFixed(2);
        const fileName = file.name;
        const re = /(\.jpg|\.jpeg|\.bmp|\.gif|\.png)$/i;

        if (!re.exec(fileName)) {
            document.querySelector('#upload-status-message').textContent = 'You suck. Your file has an unsupported extension!';
        }
        else if (fileSizeMb > 1) {        
            document.querySelector('#upload-status-message').textContent = 'You suck. Your file is too big. The file size is: ' + fileSizeMb + "MB";
            return;
        }
        else {        
            document.querySelector('#upload-status-message').textContent = 'You rock. You picked a file!!! The file size is: ' + fileSizeMb + "MB. Uploading to the cloud...";

            const formData = new FormData();
            formData.append('file', file);
            formData.append('message', messageInput);

            try {
                const response = await fetch('./upload/', {
                    method: 'POST',
                    body: formData
                });

                const result = await response.json();
                if (response.ok) {
                    document.querySelector('#upload-response-message').textContent = `We rock! File uploaded successfully: ${result.filename}`;
                    document.querySelector('#message-board').innerHTML = "";
                    readMessageFromDatabase();
                }
                else {
                    document.querySelector('#upload-response-message').textContent = `We suck. Error: ${result.detail}`;
                }
            }
            catch (error) {
                document.querySelector('#upload-response-message').textContent = `We suck. Error: ${error.message}`;
            }
            return;
        }
    });
}

async function readMessageFromDatabase(){
    //讀取DB裡面的東東render在網頁上
    const messageResponse = await fetch("/readMessages");
    const messageResponseJson = await messageResponse.json();
    // console.log(messageResponseJson);
    //從這裡開始，參考html的格式appendChild
    for (post of messageResponseJson){
        const postElement = document.createElement("div");
        postElement.classList.add("message");

        const idElement = document.createElement("div");
        idElement.classList.add("id-div");
        idElement.textContent = "Post ID: " + post.id;
        postElement.appendChild(idElement);

        const timeElement = document.createElement("div");
        timeElement.classList.add("time-div");
        timeElement.textContent = "Time created: " + post.create_time;
        postElement.appendChild(timeElement);

        const messageElement = document.createElement("div");
        messageElement.classList.add("message-div");
        messageElement.textContent = "Message: " + post.message;
        postElement.appendChild(messageElement);

        const imgElement = document.createElement("div");
        imgElement.classList.add("image-div");
        const imgBody = document.createElement("img");
        imgBody.classList.add("message-img");
        imgBody.src = post.image_url;
        imgElement.appendChild(imgBody);
        postElement.appendChild(imgElement);

        const hrElement = document.createElement("hr");
        postElement.appendChild(hrElement);

        const messageBoardElement = document.querySelector("#message-board");
        messageBoardElement.appendChild(postElement);

    }
}

readMessageFromDatabase();
addUploadButtonListener();