$(document).ready(function() {
    $("#startInput").bind("change paste", isFormValid);
    $("#duration").bind("change paste", isFormValid);
});
 
function isFormValid()
{
    var startTime = $("#startInput").val(); // 14:30
    var duration = $("#duration").val();
    var actualEnd = $("#actualEnd").val(); // 13:30
    var actualStart = $("#actualStart").val(); //12:30
    
    var disablSubmit = true;  
    
    var actualStartHour = actualStart.split(":")[0];
    var actualStartMin = actualStart.split(":")[1];
    var startDate = new Date();
    startDate.setHours(actualStartHour);
    startDate.setMinutes(actualStartMin);
    startDate.setSeconds(0);
    
    var actualEndHour = actualEnd.split(":")[0];
    var actualEndMin = actualEnd.split(":")[1];
    var endDate = new Date();
    endDate.setHours(actualEndHour);
    endDate.setMinutes(actualEndMin);
    endDate.setSeconds(0);
    
    var inputStartHour = startTime.split(":")[0];
    var inputStartMin = startTime.split(":")[1];
    var reserveStart = new Date();
    reserveStart.setHours(inputStartHour);
    reserveStart.setMinutes(inputStartMin);
    reserveStart.setSeconds(0);
    
    var reserveEnd = new Date(reserveStart);
    reserveEnd.setMinutes(reserveEnd.getMinutes() + duration);
    reserveEnd.setSeconds(0);
    
    console.log(startDate);
    console.log(endDate);
    console.log(reserveStart);
    console.log(reserveEnd);
    
    if(startDate <= reserveStart && reserveStart < endDate && startDate < reserveEnd && reserveEnd <= endDate){
        if(reserveStart.toTimeString() === reserveEnd.toTimeString() || reserveEnd < reserveStart){
            disablSubmit = true;
            
        }else{
            disablSubmit = false;
        }
    }
    if(disablSubmit && duration != ''){
        showErrorDiv(startDate, endDate,actualEnd,actualStart);
    }else{
       $('#errorDiv').prop('hidden',true);
    }
    
    $('#reserveResource').prop('disabled', disablSubmit);
}

function showErrorDiv(startDate, endDate,actualEnd,actualStart){
    $('#errorDiv').prop('hidden',false);
    var milliseconds = startDate.getTime() - endDate.getTime();
    var minutes = Math.abs(Math.floor((milliseconds/1000)/60));
    document.getElementById("errorLabel").innerHTML = "The resource is available only from "+actualStart+" to "+actualEnd;
}