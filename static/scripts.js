$(function(){ 
    
    //ajax call to edit
    var submit_post = function(to_edit, id) {
      $.getJSON($SCRIPT_ROOT + '/edit', {
        body: $(to_edit).text(),
        id: id        
      },function(data) {
        $(to_edit).text(data.result);        
      });
      return false;
    };

    //ajax call to delete    
    var delete_post = function(id, div) {
      $.getJSON($SCRIPT_ROOT + '/delete', {        
        id: id        
      },function(data) {
        $(div).hide("slow");        
      });
      return false;
    };
    

    //activates text editing on click   
    $(".activate").click(function(){

        var id = $(this).data("id");
        var to_edit = "p[data-id='" + id + "']";

        $(to_edit).css("background-color", "white");
              
        $(to_edit).prop("contenteditable","true").focus();
        
    });

    //saves text editing
    $(".save").click(function (){
        var id = $(this).data("id");
        var to_edit = "p[data-id='" + id + "']";

        var set_color = $(to_edit).closest("div").css("background-color");
        $(to_edit).css("background-color", set_color);

        submit_post(to_edit, id);
    });

    //deletes entry
    $(".delete").click(function (){
        var id = $(this).data("id");
        var to_edit = "p[data-id='" + id + "']";

        var parent = $(to_edit).parent();

        delete_post(id, parent);

    });

    
});