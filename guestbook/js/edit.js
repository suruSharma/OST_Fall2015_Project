$(document).ready(function() {
     
    $("#nameInput").bind("change", isFormValid);
    $("#startInput").bind("change", isFormValid);
    $("#endInput").bind("change", isFormValid);
    $("#tagsInput").bind("change", isFormValid);
     
});
 
function isFormValid()
{
    var originalName=$('#nameInput').val();
    var originalStartTime = $("#startInput").val();
    var originalEndTime = $("#endInput").val();
    var originalTags = $("#tagsInput").val();
    
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
    
    $('#addresource').prop('disabled', disablSubmit);
}

function hideError()
{
    $('#error-div').css("visibility", "hidden");
	
}