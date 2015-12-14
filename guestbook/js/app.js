$(document).ready(function() {
     
    $("#nameInput").bind("change paste keyup", isFormValid);
    $("#startInput").bind("change paste keyup", isFormValid);
    $("#endInput").bind("change paste keyup", isFormValid);
    $("#tagsInput").bind("change paste keyup", isFormValid);
     
});
 
function isFormValid()
{
    var name=$('#nameInput').val();
    var startTime = $("#startInput").val();
    var endTime = $("#endInput").val();
    var tags = $("#tagsInput").val();
    
    var disablSubmit = false;
    
    if(name === ''){
        disablSubmit = true;
    }
    
    if(disablSubmit == false){
        if(startTime === ''){
            disablSubmit = true;
        }
    }
    
    if(disablSubmit == false){
        if(endTime === ''){
            disablSubmit = true;
        }
    }
    
    if(disablSubmit == false && startTime != '' && endTime != ''){
        console.log(startTime)
        console.log(endTime)
        var start = startTime.split(":");
        var end = endTime.split(":");
        var input = $("endInput");
        
        if(end[0] < start[0]){
            disablSubmit = true;
            input.addClass("invalid");
        }else if(end[0] == start[0] && end[1] <= start[1]){
            disablSubmit = true;
        }
    }
    
    if(disablSubmit == false){
        if(tags === ''){
            disablSubmit = true;
        }
    }
    
    
    
    $('#addresource').prop('disabled', disablSubmit);
}

function hideError()
{
    $('#error-div').css("visibility", "hidden");
	
}