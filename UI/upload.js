function uploadFile(e) 
{
    //alert("In upload file");
    let xhr = new XMLHttpRequest();
    let formData = new FormData();
    
    formData.append("file", document.getElementById("choose_file").files[0]);
    
    xhr.onreadystatechange = function() { 
      //console.log(xhr.status); 
      //alert("Response: " + xhr.responseText);
      document.getElementById('transcript_text').innerHTML = xhr.responseText;
      } // err handling
    xhr.open("POST", 'http://127.0.0.1:8080/transcripts');    
    xhr.send(formData);
}
