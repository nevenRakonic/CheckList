
$(function(){ 
    
    var submit = function() {
      $.getJSON($SCRIPT_ROOT + '/edit/', {
        body: $("p[data-id='7']").text()        
      },function(data) {
        $("p[data-id='7']").text(data.result);        
      });
      return false;
    };

    //activates text editing on click   
    $(".activate").click(function(){

        var check = $(this).data("id");
        var to_edit = "p[data-id='" + check + "']";
              
        $(to_edit).prop("contenteditable","true").focus();
        submit();
    });

    //ajax call to edit
    
});