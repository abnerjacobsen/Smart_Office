  var table = $('#table1');

  $('#form1Btn').click(function(){
    retrievePatientData()
  });



  //------------------------------------------
  //retrieve patient appt data using their id
  //------------------------------------------
  function retrievePatientData(){

    var table = document.getElementById("table1");
    for(var i = table.rows.length - 1; i > 0; i--){
        table.deleteRow(i);
    }
    var retrieveRequest = new XMLHttpRequest();
    retrieveRequest.open("POST", "http://192.168.1.5:5001/GetPatientAppointments"); // URL ****************************
    retrieveRequest.setRequestHeader("Content-type", "application/x-www-form-urlencoded");

    retrieveRequest.onload = function() {

      if(retrieveRequest.status >= 200 && retrieveRequest.status <400){
        var ourData = JSON.parse(retrieveRequest.responseText);
        console.log(ourData);
        renderHTML(ourData);
      } else {
        window.alert("Connected to Server but error was returned, try another time");
      }
        
    };

    retrieveRequest.onerror = function() {
      window.alert("error");
    };

    retrieveRequest.send("pid="+$('#pid').val());
  }



  //------------------------------------------
  //render new table
  //------------------------------------------
  function renderHTML(data){

    var size = data.length;
    for(i = 0; i < size; i++){

      var $tr = $('<tr>').append(
          $('<td>').text(data[i].id),
          $('<td>').text(data[i].date_time),
          $('<td>').text(data[i].doctor_id),
          $('<td>').text(data[i].patient_id)
      ).appendTo(table);
    }



    //------------------------------------------
    //SELECT ROW FROM TABLE
    //------------------------------------------
    //
    //Assign click listener here, so that it applies to the new rows also.
    $("#table1 tr").click(function(){
      $(this).addClass('selected').siblings().removeClass('selected');    
      var value=$(this).find('td:first').html(); 

      displayConfirmation(value, $(this));
      });
  }

    
  
  //------------------------------------------
  //POP UP WINDOW FOR CONFIRMATION OF DELETION
  //------------------------------------------
  function displayConfirmation(apptItem, tr){

    //Get Buttons
    var deleteBtn = document.getElementById('deleteBtn');
    var cancelBtn = document.getElementById('cancelBtn');

    // Get the modal
    var model = document.getElementById('myModel');
    model.style.display = "block";

    // Get the <span> element that closes the model
    var span = document.getElementsByClassName("close")[0];

    //Get textarea and populate it
    var tArea = document.getElementById('delItems');
    tArea.value=apptItem;

    // When the user clicks on <span> (x), close the model
    span.onclick = function() {
        tArea.value = '';
        model.style.display = "none";
        tr.removeClass('selected');
    }

    // When the user clicks on delete button, delete from db, and from table.
    deleteBtn.onclick = function() {
      tArea.value = '';
      model.style.display = "none";
      postDeleteRequest(apptItem, tr);
    }

    // When the user clicks on cancel button, close the model
    cancelBtn.onclick = function() {
        tArea.value = '';
        model.style.display = "none";
        tr.removeClass('selected');
    }
  }



  //------------------------------------------
  //Send the Delete request
  //------------------------------------------
  function postDeleteRequest(apptItem, tr){
    var delRequest = new XMLHttpRequest();
    delRequest.open("POST", "http://192.168.1.5:5001/DeletePatientAppointment"); // URL ****************************
    delRequest.setRequestHeader("Content-type", "application/x-www-form-urlencoded");

    delRequest.onerror = function() {
      window.alert("error");
    };

    delRequest.send("apptID="+apptItem);

    delRequest.onload = function() {
      if(delRequest.status >= 200 && delRequest.status <400){
        var responseData = JSON.parse(delRequest.responseText);
        console.log(responseData);
        window.alert("Successfully Deleted Appt: " + apptItem);
        tr.remove();
      } else {
        window.alert("Connected to Server but error was returned, try another time");
      }
    };
  }